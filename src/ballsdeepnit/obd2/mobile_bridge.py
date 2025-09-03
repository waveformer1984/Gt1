"""
Mobile Bridge for Z-areo Non-Profit OBD2 Data Collection
=======================================================

Handles communication between mobile devices and OBD2 data collection system.
Provides real-time data streaming, remote control, and data synchronization.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

import websockets
from websockets.server import WebSocketServerProtocol
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import JSONResponse
import structlog

from .core import OBD2Manager, STANDARD_MONITORING_PARAMS
from .scanner import BidirectionalScanner
from .can_sniffer import VirtualCANSniffer

logger = structlog.get_logger(__name__)

class ConnectionType(Enum):
    WEBSOCKET = "websocket"
    HTTP_REST = "http_rest"
    BLUETOOTH = "bluetooth"
    WIFI_DIRECT = "wifi_direct"

class MessageType(Enum):
    DATA_STREAM = "data_stream"
    COMMAND = "command"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    HEARTBEAT = "heartbeat"

@dataclass
class MobileClient:
    """Mobile client connection information."""
    client_id: str
    connection_type: ConnectionType
    websocket: Optional[WebSocketServerProtocol] = None
    last_heartbeat: float = 0.0
    subscribed_parameters: Set[str] = None
    data_rate: float = 1.0  # Updates per second
    is_authenticated: bool = False
    
    def __post_init__(self):
        if self.subscribed_parameters is None:
            self.subscribed_parameters = set()
        self.last_heartbeat = time.time()

@dataclass
class MobileMessage:
    """Message structure for mobile communication."""
    message_type: MessageType
    timestamp: float
    client_id: str
    data: Dict[str, Any]
    message_id: str = None
    
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())

class MobileBridge:
    """
    Bridge between mobile devices and OBD2 data collection system.
    
    Features:
    - Real-time data streaming to mobile devices
    - Remote OBD2 scanner control
    - Data synchronization and offline support
    - Multiple connection types (WebSocket, REST API, Bluetooth)
    - Client authentication and authorization
    """
    
    def __init__(self, 
                 obd2_manager: OBD2Manager,
                 scanner: Optional[BidirectionalScanner] = None,
                 can_sniffer: Optional[VirtualCANSniffer] = None,
                 port: int = 8765):
        self.obd2_manager = obd2_manager
        self.scanner = scanner
        self.can_sniffer = can_sniffer
        self.port = port
        
        # Client management
        self.clients: Dict[str, MobileClient] = {}
        self.message_queue: List[MobileMessage] = []
        self.max_queue_size = 1000
        
        # Data streaming
        self.is_streaming = False
        self.stream_task: Optional[asyncio.Task] = None
        self.default_parameters = STANDARD_MONITORING_PARAMS.copy()
        
        # WebSocket server
        self.websocket_server = None
        
        # FastAPI for REST endpoints
        self.app = FastAPI(title="Z-areo OBD2 Mobile API")
        self._setup_rest_endpoints()
        
        # Security
        self.api_keys: Set[str] = {"zareo-nonprofit-2024"}  # Simple API key system
        
    def _setup_rest_endpoints(self):
        """Setup REST API endpoints for mobile communication."""
        
        @self.app.get("/api/status")
        async def get_status():
            """Get OBD2 system status."""
            try:
                obd2_status = self.obd2_manager.get_status()
                scanner_status = self.scanner.get_scanner_status() if self.scanner else {}
                can_status = self.can_sniffer.get_statistics() if self.can_sniffer else {}
                
                return {
                    "success": True,
                    "timestamp": time.time(),
                    "obd2": obd2_status,
                    "scanner": scanner_status,
                    "can_sniffer": can_status,
                    "connected_clients": len(self.clients)
                }
            except Exception as e:
                logger.error("Error getting status", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/parameters")
        async def get_available_parameters():
            """Get list of available OBD2 parameters."""
            try:
                parameters = self.obd2_manager.get_supported_parameters()
                return {
                    "success": True,
                    "parameters": parameters,
                    "default_monitoring": self.default_parameters
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/command")
        async def send_command(command_data: dict):
            """Send command to OBD2 system."""
            try:
                api_key = command_data.get('api_key')
                if not self._authenticate_api_key(api_key):
                    raise HTTPException(status_code=401, detail="Invalid API key")
                
                command = command_data.get('command')
                params = command_data.get('parameters', {})
                
                result = await self._execute_command(command, params)
                return {"success": True, "result": result}
                
            except Exception as e:
                logger.error("Error executing command", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/data/{parameter}")
        async def get_parameter_data(parameter: str):
            """Get current value of a specific parameter."""
            try:
                data = await self.obd2_manager.query_parameter(parameter)
                return {"success": True, "data": data}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start(self) -> bool:
        """Start the mobile bridge services."""
        try:
            logger.info("Starting mobile bridge", port=self.port)
            
            # Start WebSocket server
            await self._start_websocket_server()
            
            # Start data streaming
            await self.start_data_streaming()
            
            # Register OBD2 callbacks
            self.obd2_manager.add_data_callback(self._on_obd2_data)
            
            if self.can_sniffer:
                self.can_sniffer.add_message_callback(self._on_can_message)
            
            logger.info("Mobile bridge started successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to start mobile bridge", error=str(e))
            return False
    
    async def stop(self):
        """Stop the mobile bridge services."""
        try:
            # Stop data streaming
            await self.stop_data_streaming()
            
            # Disconnect all clients
            for client in list(self.clients.values()):
                await self._disconnect_client(client.client_id)
            
            # Stop WebSocket server
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
            
            logger.info("Mobile bridge stopped")
            
        except Exception as e:
            logger.error("Error stopping mobile bridge", error=str(e))
    
    async def _start_websocket_server(self):
        """Start WebSocket server for real-time communication."""
        try:
            self.websocket_server = await websockets.serve(
                self._handle_websocket_connection,
                "localhost",
                self.port
            )
            logger.info("WebSocket server started", port=self.port)
        except Exception as e:
            logger.error("Failed to start WebSocket server", error=str(e))
            raise
    
    async def _handle_websocket_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection from mobile client."""
        client_id = str(uuid.uuid4())
        client = MobileClient(
            client_id=client_id,
            connection_type=ConnectionType.WEBSOCKET,
            websocket=websocket
        )
        
        try:
            self.clients[client_id] = client
            logger.info("New mobile client connected", client_id=client_id)
            
            # Send welcome message
            welcome_msg = MobileMessage(
                message_type=MessageType.STATUS_UPDATE,
                timestamp=time.time(),
                client_id=client_id,
                data={
                    "status": "connected",
                    "available_parameters": self.obd2_manager.get_supported_parameters(),
                    "default_monitoring": self.default_parameters
                }
            )
            await self._send_message_to_client(client_id, welcome_msg)
            
            # Handle incoming messages
            async for message in websocket:
                await self._handle_client_message(client_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Mobile client disconnected", client_id=client_id)
        except Exception as e:
            logger.error("Error handling WebSocket connection", client_id=client_id, error=str(e))
        finally:
            await self._disconnect_client(client_id)
    
    async def _handle_client_message(self, client_id: str, message: str):
        """Handle message from mobile client."""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            client = self.clients.get(client_id)
            if not client:
                return
            
            # Update heartbeat
            client.last_heartbeat = time.time()
            
            if msg_type == 'subscribe':
                # Subscribe to parameters
                parameters = data.get('parameters', [])
                data_rate = data.get('data_rate', 1.0)
                
                client.subscribed_parameters.update(parameters)
                client.data_rate = max(0.1, min(10.0, data_rate))  # Limit rate
                
                logger.info("Client subscribed to parameters", 
                           client_id=client_id, 
                           parameters=parameters,
                           data_rate=data_rate)
            
            elif msg_type == 'unsubscribe':
                # Unsubscribe from parameters
                parameters = data.get('parameters', [])
                client.subscribed_parameters.difference_update(parameters)
                
            elif msg_type == 'command':
                # Execute command
                command = data.get('command')
                params = data.get('parameters', {})
                
                if not client.is_authenticated:
                    api_key = data.get('api_key')
                    if self._authenticate_api_key(api_key):
                        client.is_authenticated = True
                    else:
                        await self._send_error_to_client(client_id, "Authentication required")
                        return
                
                result = await self._execute_command(command, params)
                
                response_msg = MobileMessage(
                    message_type=MessageType.COMMAND,
                    timestamp=time.time(),
                    client_id=client_id,
                    data={'command': command, 'result': result}
                )
                await self._send_message_to_client(client_id, response_msg)
            
            elif msg_type == 'heartbeat':
                # Respond to heartbeat
                heartbeat_msg = MobileMessage(
                    message_type=MessageType.HEARTBEAT,
                    timestamp=time.time(),
                    client_id=client_id,
                    data={'status': 'alive'}
                )
                await self._send_message_to_client(client_id, heartbeat_msg)
                
        except Exception as e:
            logger.error("Error handling client message", client_id=client_id, error=str(e))
            await self._send_error_to_client(client_id, f"Message handling error: {str(e)}")
    
    async def _execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command from mobile client."""
        try:
            if command == 'start_monitoring':
                parameters = params.get('parameters', self.default_parameters)
                interval = params.get('interval', 1.0)
                
                await self.obd2_manager.start_monitoring(parameters, interval)
                return {'success': True, 'message': 'Monitoring started'}
            
            elif command == 'stop_monitoring':
                await self.obd2_manager.stop_monitoring()
                return {'success': True, 'message': 'Monitoring stopped'}
            
            elif command == 'read_codes' and self.scanner:
                codes = await self.scanner.read_diagnostic_codes()
                return {'success': True, 'codes': [asdict(code) for code in codes]}
            
            elif command == 'clear_codes' and self.scanner:
                success = await self.scanner.clear_diagnostic_codes()
                return {'success': success, 'message': 'Codes cleared' if success else 'Failed to clear codes'}
            
            elif command == 'actuator_test' and self.scanner:
                actuator = params.get('actuator')
                test_params = params.get('test_parameters', {})
                
                if not actuator:
                    return {'success': False, 'error': 'Actuator not specified'}
                
                result = await self.scanner.perform_actuator_test(actuator, test_params)
                return result
            
            elif command == 'query_parameter':
                parameter = params.get('parameter')
                if not parameter:
                    return {'success': False, 'error': 'Parameter not specified'}
                
                data = await self.obd2_manager.query_parameter(parameter)
                return {'success': True, 'data': data}
            
            else:
                return {'success': False, 'error': f'Unknown command: {command}'}
                
        except Exception as e:
            logger.error("Error executing command", command=command, error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def start_data_streaming(self):
        """Start streaming data to connected clients."""
        if self.is_streaming:
            return
        
        self.is_streaming = True
        self.stream_task = asyncio.create_task(self._data_stream_loop())
        logger.info("Data streaming started")
    
    async def stop_data_streaming(self):
        """Stop streaming data to clients."""
        self.is_streaming = False
        if self.stream_task:
            self.stream_task.cancel()
            try:
                await self.stream_task
            except asyncio.CancelledError:
                pass
            self.stream_task = None
        logger.info("Data streaming stopped")
    
    async def _data_stream_loop(self):
        """Main data streaming loop."""
        last_stream_times = {}
        
        while self.is_streaming:
            try:
                current_time = time.time()
                
                for client_id, client in self.clients.items():
                    if not client.subscribed_parameters:
                        continue
                    
                    # Check if it's time to send data to this client
                    last_time = last_stream_times.get(client_id, 0)
                    if current_time - last_time < (1.0 / client.data_rate):
                        continue
                    
                    # Collect data for subscribed parameters
                    data_batch = {}
                    for param in client.subscribed_parameters:
                        try:
                            data = await self.obd2_manager.query_parameter(param)
                            if data:
                                data_batch[param] = data
                        except Exception as e:
                            logger.debug("Error querying parameter for stream", param=param, error=str(e))
                    
                    if data_batch:
                        stream_msg = MobileMessage(
                            message_type=MessageType.DATA_STREAM,
                            timestamp=current_time,
                            client_id=client_id,
                            data=data_batch
                        )
                        await self._send_message_to_client(client_id, stream_msg)
                        last_stream_times[client_id] = current_time
                
                await asyncio.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                logger.error("Error in data stream loop", error=str(e))
                await asyncio.sleep(1.0)
    
    async def _on_obd2_data(self, data_batch: Dict[str, Any]):
        """Handle OBD2 data callback."""
        try:
            # Broadcast to interested clients
            for client_id, client in self.clients.items():
                relevant_data = {}
                for param, data in data_batch.items():
                    if param in client.subscribed_parameters:
                        relevant_data[param] = data
                
                if relevant_data:
                    msg = MobileMessage(
                        message_type=MessageType.DATA_STREAM,
                        timestamp=time.time(),
                        client_id=client_id,
                        data=relevant_data
                    )
                    await self._send_message_to_client(client_id, msg)
                    
        except Exception as e:
            logger.error("Error handling OBD2 data callback", error=str(e))
    
    async def _on_can_message(self, can_msg):
        """Handle CAN message callback."""
        try:
            # Only send CAN data to authenticated clients
            for client_id, client in self.clients.items():
                if client.is_authenticated and 'can_messages' in client.subscribed_parameters:
                    msg = MobileMessage(
                        message_type=MessageType.DATA_STREAM,
                        timestamp=time.time(),
                        client_id=client_id,
                        data={
                            'can_message': {
                                'arbitration_id': f"0x{can_msg.arbitration_id:X}",
                                'data': can_msg.data.hex(),
                                'protocol': can_msg.protocol.value if can_msg.protocol else None,
                                'decoded_data': can_msg.decoded_data
                            }
                        }
                    )
                    await self._send_message_to_client(client_id, msg)
                    
        except Exception as e:
            logger.error("Error handling CAN message callback", error=str(e))
    
    async def _send_message_to_client(self, client_id: str, message: MobileMessage):
        """Send message to specific client."""
        try:
            client = self.clients.get(client_id)
            if not client or not client.websocket:
                return
            
            message_data = {
                'type': message.message_type.value,
                'timestamp': message.timestamp,
                'message_id': message.message_id,
                'data': message.data
            }
            
            await client.websocket.send(json.dumps(message_data))
            
        except Exception as e:
            logger.error("Error sending message to client", client_id=client_id, error=str(e))
            await self._disconnect_client(client_id)
    
    async def _send_error_to_client(self, client_id: str, error_message: str):
        """Send error message to client."""
        error_msg = MobileMessage(
            message_type=MessageType.ERROR,
            timestamp=time.time(),
            client_id=client_id,
            data={'error': error_message}
        )
        await self._send_message_to_client(client_id, error_msg)
    
    async def _disconnect_client(self, client_id: str):
        """Disconnect and remove client."""
        try:
            if client_id in self.clients:
                client = self.clients[client_id]
                if client.websocket:
                    await client.websocket.close()
                del self.clients[client_id]
                logger.info("Client disconnected", client_id=client_id)
        except Exception as e:
            logger.error("Error disconnecting client", client_id=client_id, error=str(e))
    
    def _authenticate_api_key(self, api_key: str) -> bool:
        """Authenticate API key."""
        return api_key in self.api_keys
    
    def get_bridge_status(self) -> Dict[str, Any]:
        """Get mobile bridge status."""
        return {
            'is_running': self.websocket_server is not None,
            'is_streaming': self.is_streaming,
            'connected_clients': len(self.clients),
            'port': self.port,
            'clients': [
                {
                    'client_id': client.client_id,
                    'connection_type': client.connection_type.value,
                    'subscribed_parameters': list(client.subscribed_parameters),
                    'data_rate': client.data_rate,
                    'is_authenticated': client.is_authenticated,
                    'last_heartbeat': client.last_heartbeat
                }
                for client in self.clients.values()
            ]
        }