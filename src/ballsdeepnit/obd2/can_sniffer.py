"""
Virtual CAN Sniffer for Z-areo Non-Profit OBD2 Data Collection
==============================================================

Advanced CAN bus protocol analysis and message sniffing capabilities.
Integrates with OBD2 system for comprehensive vehicle communication monitoring.
"""

import asyncio
import time
import struct
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

import can
import cantools
from can.interface import Bus
from can.message import Message
import structlog

logger = structlog.get_logger(__name__)

class CANProtocol(Enum):
    ISO_14230_4 = "iso14230-4"  # KWP2000
    ISO_15765_2 = "iso15765-2"  # CAN-TP
    J1939 = "j1939"
    UDS = "uds"  # Unified Diagnostic Services
    OBD2 = "obd2"
    CUSTOM = "custom"

@dataclass
class CANFilter:
    """CAN message filter configuration."""
    can_id: int
    mask: int = 0x7FF
    extended: bool = False
    enabled: bool = True

@dataclass 
class CANMessage:
    """Parsed CAN message with metadata."""
    arbitration_id: int
    data: bytes
    timestamp: float
    is_extended: bool = False
    is_error: bool = False
    is_remote: bool = False
    channel: Optional[str] = None
    dlc: int = 0
    
    # Protocol analysis
    protocol: Optional[CANProtocol] = None
    service_id: Optional[int] = None
    pid: Optional[int] = None
    decoded_data: Optional[Dict[str, Any]] = None

@dataclass
class SnifferStats:
    """CAN sniffer statistics."""
    total_messages: int = 0
    messages_per_second: float = 0.0
    unique_ids: Set[int] = field(default_factory=set)
    protocol_counts: Dict[str, int] = field(default_factory=dict)
    error_count: int = 0
    last_reset: float = field(default_factory=time.time)

class VirtualCANSniffer:
    """
    Advanced virtual CAN bus sniffer with protocol analysis.
    
    Features:
    - Multi-interface CAN bus monitoring
    - Real-time protocol analysis (OBD2, UDS, J1939)
    - Message filtering and decoding
    - Statistical analysis and reporting
    - Integration with OBD2 data collection
    """
    
    def __init__(self, interface: str = "virtual", channel: str = "vcan0"):
        self.interface = interface
        self.channel = channel
        self.bus: Optional[Bus] = None
        self.is_running = False
        
        # Message handling
        self.message_callbacks: List[Callable] = []
        self.filters: List[CANFilter] = []
        self.message_buffer: List[CANMessage] = []
        self.buffer_size = 10000
        
        # Protocol analysis
        self.protocol_analyzers: Dict[CANProtocol, Callable] = {
            CANProtocol.OBD2: self._analyze_obd2,
            CANProtocol.UDS: self._analyze_uds,
            CANProtocol.J1939: self._analyze_j1939
        }
        
        # Statistics
        self.stats = SnifferStats()
        self.stats_interval = 1.0
        self._stats_task: Optional[asyncio.Task] = None
        
        # Threading
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._receive_task: Optional[asyncio.Task] = None
        
    async def start(self) -> bool:
        """Start the CAN sniffer."""
        try:
            logger.info("Starting CAN sniffer", interface=self.interface, channel=self.channel)
            
            # Initialize CAN bus
            self.bus = can.interface.Bus(
                channel=self.channel,
                interface=self.interface,
                receive_own_messages=False
            )
            
            if not self.bus:
                logger.error("Failed to initialize CAN bus")
                return False
            
            self.is_running = True
            
            # Start message receiving task
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            # Start statistics task
            self._stats_task = asyncio.create_task(self._stats_loop())
            
            logger.info("CAN sniffer started successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to start CAN sniffer", error=str(e))
            return False
    
    async def stop(self):
        """Stop the CAN sniffer."""
        try:
            self.is_running = False
            
            # Cancel tasks
            if self._receive_task:
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
            
            if self._stats_task:
                self._stats_task.cancel()
                try:
                    await self._stats_task
                except asyncio.CancelledError:
                    pass
            
            # Close bus
            if self.bus:
                self.bus.shutdown()
                self.bus = None
            
            logger.info("CAN sniffer stopped")
            
        except Exception as e:
            logger.error("Error stopping CAN sniffer", error=str(e))
    
    async def _receive_loop(self):
        """Main message receiving loop."""
        while self.is_running and self.bus:
            try:
                # Receive message (non-blocking)
                msg = await asyncio.get_event_loop().run_in_executor(
                    self._executor, self._receive_message
                )
                
                if msg:
                    await self._process_message(msg)
                else:
                    await asyncio.sleep(0.001)  # Small delay if no message
                    
            except Exception as e:
                logger.error("Error in receive loop", error=str(e))
                await asyncio.sleep(0.1)
    
    def _receive_message(self) -> Optional[Message]:
        """Receive a single CAN message."""
        try:
            if self.bus:
                return self.bus.recv(timeout=0.01)
        except Exception as e:
            logger.debug("Message receive error", error=str(e))
        return None
    
    async def _process_message(self, raw_msg: Message):
        """Process and analyze a received CAN message."""
        try:
            # Convert to internal format
            can_msg = CANMessage(
                arbitration_id=raw_msg.arbitration_id,
                data=raw_msg.data,
                timestamp=raw_msg.timestamp or time.time(),
                is_extended=raw_msg.is_extended_id,
                is_error=raw_msg.is_error_frame,
                is_remote=raw_msg.is_remote_frame,
                channel=getattr(raw_msg, 'channel', self.channel),
                dlc=raw_msg.dlc
            )
            
            # Apply filters
            if not self._passes_filters(can_msg):
                return
            
            # Protocol analysis
            await self._analyze_protocol(can_msg)
            
            # Update statistics
            self._update_stats(can_msg)
            
            # Add to buffer
            self._add_to_buffer(can_msg)
            
            # Notify callbacks
            for callback in self.message_callbacks:
                try:
                    await callback(can_msg)
                except Exception as e:
                    logger.error("Error in message callback", error=str(e))
                    
        except Exception as e:
            logger.error("Error processing CAN message", error=str(e))
    
    def _passes_filters(self, msg: CANMessage) -> bool:
        """Check if message passes configured filters."""
        if not self.filters:
            return True
            
        for filter_rule in self.filters:
            if not filter_rule.enabled:
                continue
                
            if (msg.arbitration_id & filter_rule.mask) == (filter_rule.can_id & filter_rule.mask):
                if filter_rule.extended == msg.is_extended:
                    return True
                    
        return False
    
    async def _analyze_protocol(self, msg: CANMessage):
        """Analyze message protocol and decode if possible."""
        # OBD2 detection (standard IDs: 0x7E0-0x7E7, 0x7E8-0x7EF)
        if 0x7E0 <= msg.arbitration_id <= 0x7EF:
            msg.protocol = CANProtocol.OBD2
            await self._analyze_obd2(msg)
        
        # UDS detection (0x700-0x7FF range commonly used)
        elif 0x700 <= msg.arbitration_id <= 0x7FF:
            msg.protocol = CANProtocol.UDS
            await self._analyze_uds(msg)
        
        # J1939 detection (29-bit extended IDs)
        elif msg.is_extended and msg.arbitration_id > 0x10000000:
            msg.protocol = CANProtocol.J1939
            await self._analyze_j1939(msg)
        
        else:
            msg.protocol = CANProtocol.CUSTOM
    
    async def _analyze_obd2(self, msg: CANMessage):
        """Analyze OBD2 protocol messages."""
        try:
            if len(msg.data) < 2:
                return
                
            # Parse service ID and PID
            if msg.arbitration_id <= 0x7E7:  # Request
                msg.service_id = msg.data[1] if len(msg.data) > 1 else None
                msg.pid = msg.data[2] if len(msg.data) > 2 else None
                
            else:  # Response (0x7E8-0x7EF)
                if msg.data[1] >= 0x40:  # Positive response
                    msg.service_id = msg.data[1] - 0x40
                    msg.pid = msg.data[2] if len(msg.data) > 2 else None
                    
                    # Decode common PIDs
                    msg.decoded_data = self._decode_obd2_pid(msg.service_id, msg.pid, msg.data[3:])
                    
        except Exception as e:
            logger.debug("OBD2 analysis error", error=str(e))
    
    async def _analyze_uds(self, msg: CANMessage):
        """Analyze UDS (Unified Diagnostic Services) messages."""
        try:
            if len(msg.data) < 1:
                return
                
            service_id = msg.data[0]
            
            # UDS service identification
            uds_services = {
                0x10: "DiagnosticSessionControl",
                0x11: "ECUReset", 
                0x22: "ReadDataByIdentifier",
                0x23: "ReadMemoryByAddress",
                0x27: "SecurityAccess",
                0x2E: "WriteDataByIdentifier",
                0x31: "RoutineControl",
                0x34: "RequestDownload",
                0x36: "TransferData",
                0x37: "RequestTransferExit"
            }
            
            msg.service_id = service_id
            msg.decoded_data = {
                'service_name': uds_services.get(service_id, f"Unknown_0x{service_id:02X}"),
                'raw_data': msg.data[1:].hex()
            }
            
        except Exception as e:
            logger.debug("UDS analysis error", error=str(e))
    
    async def _analyze_j1939(self, msg: CANMessage):
        """Analyze J1939 protocol messages."""
        try:
            # Extract J1939 fields from 29-bit ID
            priority = (msg.arbitration_id >> 26) & 0x7
            pgn = (msg.arbitration_id >> 8) & 0x3FFFF
            source_addr = msg.arbitration_id & 0xFF
            
            msg.decoded_data = {
                'priority': priority,
                'pgn': pgn,
                'source_address': source_addr,
                'pgn_hex': f"0x{pgn:05X}"
            }
            
        except Exception as e:
            logger.debug("J1939 analysis error", error=str(e))
    
    def _decode_obd2_pid(self, service: int, pid: int, data: bytes) -> Dict[str, Any]:
        """Decode OBD2 PID data."""
        if service != 1 or not data:  # Only handle Mode 01 for now
            return {}
            
        try:
            # Common PID decodings
            if pid == 0x0C and len(data) >= 2:  # Engine RPM
                rpm = ((data[0] << 8) + data[1]) / 4
                return {'parameter': 'RPM', 'value': rpm, 'unit': 'rpm'}
                
            elif pid == 0x0D and len(data) >= 1:  # Vehicle Speed
                speed = data[0]
                return {'parameter': 'SPEED', 'value': speed, 'unit': 'km/h'}
                
            elif pid == 0x05 and len(data) >= 1:  # Coolant Temperature
                temp = data[0] - 40
                return {'parameter': 'COOLANT_TEMP', 'value': temp, 'unit': '°C'}
                
            elif pid == 0x11 and len(data) >= 1:  # Throttle Position
                throttle = (data[0] * 100) / 255
                return {'parameter': 'THROTTLE_POS', 'value': throttle, 'unit': '%'}
                
        except Exception as e:
            logger.debug("PID decode error", pid=pid, error=str(e))
            
        return {'raw_data': data.hex()}
    
    def _update_stats(self, msg: CANMessage):
        """Update sniffer statistics."""
        self.stats.total_messages += 1
        self.stats.unique_ids.add(msg.arbitration_id)
        
        if msg.protocol:
            protocol_name = msg.protocol.value
            self.stats.protocol_counts[protocol_name] = \
                self.stats.protocol_counts.get(protocol_name, 0) + 1
        
        if msg.is_error:
            self.stats.error_count += 1
    
    def _add_to_buffer(self, msg: CANMessage):
        """Add message to circular buffer."""
        self.message_buffer.append(msg)
        if len(self.message_buffer) > self.buffer_size:
            self.message_buffer.pop(0)
    
    async def _stats_loop(self):
        """Calculate and update statistics periodically."""
        last_count = 0
        
        while self.is_running:
            try:
                await asyncio.sleep(self.stats_interval)
                
                current_count = self.stats.total_messages
                self.stats.messages_per_second = (current_count - last_count) / self.stats_interval
                last_count = current_count
                
            except Exception as e:
                logger.error("Error in stats loop", error=str(e))
    
    def add_filter(self, can_id: int, mask: int = 0x7FF, extended: bool = False):
        """Add a CAN message filter."""
        filter_rule = CANFilter(can_id=can_id, mask=mask, extended=extended)
        self.filters.append(filter_rule)
        logger.info("Added CAN filter", can_id=f"0x{can_id:X}", mask=f"0x{mask:X}")
    
    def remove_filter(self, can_id: int):
        """Remove a CAN message filter."""
        self.filters = [f for f in self.filters if f.can_id != can_id]
        logger.info("Removed CAN filter", can_id=f"0x{can_id:X}")
    
    def clear_filters(self):
        """Clear all CAN message filters."""
        self.filters.clear()
        logger.info("Cleared all CAN filters")
    
    def add_message_callback(self, callback: Callable):
        """Add callback for received messages."""
        self.message_callbacks.append(callback)
    
    def remove_message_callback(self, callback: Callable):
        """Remove message callback."""
        if callback in self.message_callbacks:
            self.message_callbacks.remove(callback)
    
    def get_recent_messages(self, count: int = 100) -> List[CANMessage]:
        """Get recent messages from buffer."""
        return self.message_buffer[-count:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current sniffer statistics."""
        return {
            'total_messages': self.stats.total_messages,
            'messages_per_second': self.stats.messages_per_second,
            'unique_ids': len(self.stats.unique_ids),
            'protocol_counts': dict(self.stats.protocol_counts),
            'error_count': self.stats.error_count,
            'uptime': time.time() - self.stats.last_reset,
            'buffer_size': len(self.message_buffer)
        }
    
    def reset_statistics(self):
        """Reset all statistics."""
        self.stats = SnifferStats()
        logger.info("Reset CAN sniffer statistics")

# Predefined filter sets for common use cases
OBD2_FILTERS = [
    CANFilter(can_id=0x7E0, mask=0x7F8),  # OBD2 requests
    CANFilter(can_id=0x7E8, mask=0x7F8),  # OBD2 responses
]

UDS_FILTERS = [
    CANFilter(can_id=0x700, mask=0x700),  # Common UDS range
]

J1939_FILTERS = [
    CANFilter(can_id=0x18FEF100, mask=0x1FFFF00, extended=True),  # J1939 PGN range
]