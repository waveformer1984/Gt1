"""
Core OBD2 Manager for Z-areo Non-Profit Data Collection
======================================================

Manages OBD2 adapters, connections, and basic vehicle communication.
Supports ELM327, STN1110, and other common OBD2 interfaces.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

import obd
import serial
import can
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

class AdapterType(Enum):
    ELM327_SERIAL = "elm327_serial"
    ELM327_BLUETOOTH = "elm327_bluetooth"
    ELM327_WIFI = "elm327_wifi"
    STN1110 = "stn1110"
    CANDUMP = "candump"
    VIRTUAL = "virtual"

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

@dataclass
class VehicleInfo:
    vin: Optional[str] = None
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    engine: Optional[str] = None
    fuel_type: Optional[str] = None
    supported_pids: List[str] = None

class OBD2Config(BaseModel):
    adapter_type: AdapterType = AdapterType.ELM327_SERIAL
    port: str = "/dev/ttyUSB0"
    baudrate: int = 38400
    timeout: float = 30.0
    auto_connect: bool = True
    fast_mode: bool = True
    protocol: Optional[str] = None
    can_filters: List[Dict[str, Any]] = Field(default_factory=list)

class OBD2Manager:
    """
    Core OBD2 manager for vehicle data collection.
    
    Features:
    - Multiple adapter support (ELM327, STN1110, etc.)
    - Async operation for non-blocking data collection
    - Automatic reconnection and error recovery
    - Real-time data streaming
    - Vehicle identification and capabilities detection
    """
    
    def __init__(self, config: OBD2Config):
        self.config = config
        self.connection: Optional[obd.OBD] = None
        self.status = ConnectionStatus.DISCONNECTED
        self.vehicle_info = VehicleInfo()
        self.supported_commands: Dict[str, obd.OBDCommand] = {}
        self.data_callbacks: List[Callable] = []
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def connect(self) -> bool:
        """Connect to OBD2 adapter and vehicle."""
        try:
            self.status = ConnectionStatus.CONNECTING
            logger.info("Connecting to OBD2 adapter", 
                       adapter=self.config.adapter_type.value,
                       port=self.config.port)
            
            # Configure OBD library
            obd.logger.setLevel(logging.WARNING)
            
            # Attempt connection based on adapter type
            if self.config.adapter_type == AdapterType.ELM327_SERIAL:
                self.connection = obd.OBD(
                    portstr=self.config.port,
                    baudrate=self.config.baudrate,
                    timeout=self.config.timeout,
                    fast=self.config.fast_mode,
                    protocol=self.config.protocol
                )
            elif self.config.adapter_type == AdapterType.ELM327_BLUETOOTH:
                # Bluetooth connection handling
                self.connection = obd.OBD(
                    portstr=self.config.port,  # Bluetooth device path
                    timeout=self.config.timeout,
                    fast=self.config.fast_mode
                )
            else:
                raise ValueError(f"Unsupported adapter type: {self.config.adapter_type}")
            
            if self.connection and self.connection.is_connected():
                self.status = ConnectionStatus.CONNECTED
                await self._initialize_vehicle()
                logger.info("Successfully connected to vehicle",
                           vin=self.vehicle_info.vin,
                           supported_pids=len(self.supported_commands))
                return True
            else:
                self.status = ConnectionStatus.ERROR
                logger.error("Failed to connect to OBD2 adapter")
                return False
                
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            logger.error("OBD2 connection error", error=str(e))
            return False
    
    async def _initialize_vehicle(self):
        """Initialize vehicle information and supported commands."""
        if not self.connection:
            return
            
        try:
            # Get VIN
            vin_cmd = obd.commands.VIN
            if vin_cmd in self.connection.supported_commands:
                response = self.connection.query(vin_cmd)
                if response and response.value:
                    self.vehicle_info.vin = response.value
            
            # Get supported PIDs
            self.supported_commands = {}
            for cmd in self.connection.supported_commands:
                self.supported_commands[cmd.name] = cmd
                
            # Try to get additional vehicle info
            if obd.commands.FUEL_TYPE in self.connection.supported_commands:
                response = self.connection.query(obd.commands.FUEL_TYPE)
                if response and response.value:
                    self.vehicle_info.fuel_type = str(response.value)
                    
        except Exception as e:
            logger.warning("Error initializing vehicle info", error=str(e))
    
    async def disconnect(self):
        """Disconnect from OBD2 adapter."""
        try:
            if self.is_monitoring:
                await self.stop_monitoring()
                
            if self.connection:
                self.connection.close()
                self.connection = None
                
            self.status = ConnectionStatus.DISCONNECTED
            logger.info("Disconnected from OBD2 adapter")
            
        except Exception as e:
            logger.error("Error disconnecting OBD2", error=str(e))
    
    async def query_parameter(self, parameter: str) -> Optional[Any]:
        """Query a specific OBD2 parameter."""
        if not self.connection or not self.connection.is_connected():
            return None
            
        try:
            if parameter in self.supported_commands:
                cmd = self.supported_commands[parameter]
                response = self.connection.query(cmd)
                if response and not response.is_null():
                    return {
                        'parameter': parameter,
                        'value': response.value,
                        'unit': str(response.unit) if response.unit else None,
                        'timestamp': time.time()
                    }
        except Exception as e:
            logger.error("Error querying parameter", parameter=parameter, error=str(e))
            
        return None
    
    async def start_monitoring(self, parameters: List[str], interval: float = 1.0):
        """Start continuous monitoring of specified parameters."""
        if self.is_monitoring:
            await self.stop_monitoring()
            
        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(
            self._monitor_loop(parameters, interval)
        )
        logger.info("Started OBD2 monitoring", parameters=parameters)
    
    async def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        logger.info("Stopped OBD2 monitoring")
    
    async def _monitor_loop(self, parameters: List[str], interval: float):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                data_batch = {}
                timestamp = time.time()
                
                for param in parameters:
                    data = await self.query_parameter(param)
                    if data:
                        data_batch[param] = data
                
                if data_batch:
                    # Notify all registered callbacks
                    for callback in self.data_callbacks:
                        try:
                            await callback(data_batch)
                        except Exception as e:
                            logger.error("Error in data callback", error=str(e))
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(1.0)  # Back off on error
    
    def add_data_callback(self, callback: Callable):
        """Add a callback function to receive monitoring data."""
        self.data_callbacks.append(callback)
    
    def remove_data_callback(self, callback: Callable):
        """Remove a data callback function."""
        if callback in self.data_callbacks:
            self.data_callbacks.remove(callback)
    
    def get_supported_parameters(self) -> List[str]:
        """Get list of supported OBD2 parameters."""
        return list(self.supported_commands.keys())
    
    def get_status(self) -> Dict[str, Any]:
        """Get current connection and vehicle status."""
        return {
            'connection_status': self.status.value,
            'adapter_type': self.config.adapter_type.value,
            'port': self.config.port,
            'is_monitoring': self.is_monitoring,
            'vehicle_info': {
                'vin': self.vehicle_info.vin,
                'fuel_type': self.vehicle_info.fuel_type,
                'supported_parameters': len(self.supported_commands)
            }
        }

# Common OBD2 parameters for monitoring
STANDARD_MONITORING_PARAMS = [
    'RPM',
    'SPEED',
    'THROTTLE_POS',
    'ENGINE_LOAD',
    'COOLANT_TEMP',
    'FUEL_LEVEL',
    'INTAKE_TEMP',
    'MAF',
    'FUEL_TRIM_1',
    'FUEL_TRIM_2'
]