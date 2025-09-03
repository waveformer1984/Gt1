"""
OBD2 routes for bidirectional data gathering and scanner operations.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import json

import structlog

from ..obd2.zareo_system import ZareoOBD2System, ZareoSystemConfig
from ..obd2.scanner import BidirectionalScanner, ScannerMode, DiagnosticTest
from ..obd2.core import AdapterType
from .auth_routes import get_current_user, get_current_admin_user
from ..auth.models import User

logger = structlog.get_logger(__name__)

# Pydantic models for requests/responses
class StartSessionRequest(BaseModel):
    session_name: str
    participant_id: Optional[str] = None
    adapter_type: str = "ELM327_SERIAL"
    port: str = "/dev/ttyUSB0"
    enable_can_sniffer: bool = True
    enable_mobile_bridge: bool = True

class DiagnosticRequest(BaseModel):
    test_type: str = "full"
    save_results: bool = True

class ActuatorTestRequest(BaseModel):
    actuator_name: str
    parameters: Dict[str, Any]

class OBD2CommandRequest(BaseModel):
    command: str
    parameters: Optional[Dict[str, Any]] = None

class ScannerConfigRequest(BaseModel):
    mode: str = "read_only"
    enable_bidirectional: bool = False

# Global system instance (in production, this would be properly managed)
_zareo_system: Optional[ZareoOBD2System] = None
_active_sessions: Dict[str, Dict[str, Any]] = {}
_websocket_connections: List[WebSocket] = []

# Create router
router = APIRouter(prefix="/api/obd2", tags=["obd2"])

async def get_zareo_system() -> ZareoOBD2System:
    """Get or create the Z-areo OBD2 system instance."""
    global _zareo_system
    if _zareo_system is None:
        config = ZareoSystemConfig()
        _zareo_system = ZareoOBD2System(config)
        await _zareo_system.initialize()
    return _zareo_system

async def check_obd2_permission(user: User, permission: str) -> bool:
    """Check if user has OBD2 permission."""
    if user.admin_profile:
        return user.admin_profile.has_obd2_permission(permission)
    return False

@router.get("/status")
async def get_obd2_status(
    current_user: User = Depends(get_current_user),
    zareo_system: ZareoOBD2System = Depends(get_zareo_system)
):
    """Get current OBD2 system status."""
    try:
        if not await check_obd2_permission(current_user, "read_data"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="OBD2 read permission required"
            )
        
        system_status = {
            "is_running": zareo_system.is_running,
            "current_session_id": zareo_system.current_session_id,
            "system_stats": zareo_system.system_stats,
            "components": {
                "obd2_manager": zareo_system.obd2_manager is not None,
                "scanner": zareo_system.scanner is not None,
                "can_sniffer": zareo_system.can_sniffer is not None,
                "mobile_bridge": zareo_system.mobile_bridge is not None,
                "data_collector": zareo_system.data_collector is not None
            }
        }
        
        # Add connection status if OBD2 manager exists
        if zareo_system.obd2_manager:
            system_status["connection_status"] = zareo_system.obd2_manager.connection_status.value
            system_status["adapter_info"] = {
                "type": zareo_system.obd2_manager.config.adapter_type.value,
                "port": zareo_system.obd2_manager.config.port
            }
        
        return system_status
        
    except Exception as e:
        logger.error(f"Failed to get OBD2 status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system status"
        )

@router.post("/start-session")
async def start_obd2_session(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    zareo_system: ZareoOBD2System = Depends(get_zareo_system)
):
    """Start a new OBD2 data collection session."""
    try:
        if not await check_obd2_permission(current_user, "read_data"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="OBD2 read permission required"
            )
        
        # Update system configuration if needed
        try:
            adapter_type = AdapterType(request.adapter_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid adapter type"
            )
        
        zareo_system.config.obd2_adapter_type = adapter_type
        zareo_system.config.obd2_port = request.port
        zareo_system.config.enable_can_sniffer = request.enable_can_sniffer
        zareo_system.config.enable_mobile_bridge = request.enable_mobile_bridge
        
        # Start the system if not running
        if not zareo_system.is_running:
            if not await zareo_system.start():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to start OBD2 system"
                )
        
        # Start data collection session
        session_id = await zareo_system.start_data_collection_session(
            session_name=request.session_name,
            participant_id=request.participant_id or f"user_{current_user.id}"
        )
        
        # Track active session
        _active_sessions[session_id] = {
            "user_id": current_user.id,
            "session_name": request.session_name,
            "start_time": datetime.utcnow().isoformat(),
            "adapter_type": request.adapter_type,
            "port": request.port
        }
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "OBD2 session started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start OBD2 session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start session"
        )

@router.post("/stop-session")
async def stop_obd2_session(
    current_user: User = Depends(get_current_user),
    zareo_system: ZareoOBD2System = Depends(get_zareo_system)
):
    """Stop the current OBD2 data collection session."""
    try:
        if not zareo_system.current_session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active session to stop"
            )
        
        # Check if user owns this session
        session_info = _active_sessions.get(zareo_system.current_session_id)
        if session_info and session_info["user_id"] != current_user.id:
            if not await check_obd2_permission(current_user, "system_configuration"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot stop session owned by another user"
                )
        
        result = await zareo_system.stop_data_collection_session()
        
        # Remove from active sessions
        if zareo_system.current_session_id in _active_sessions:
            del _active_sessions[zareo_system.current_session_id]
        
        return {
            "success": result["success"],
            "message": "Session stopped successfully",
            "session_summary": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop OBD2 session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop session"
        )

@router.post("/diagnostic")
async def perform_diagnostic(
    request: DiagnosticRequest,
    current_user: User = Depends(get_current_user),
    zareo_system: ZareoOBD2System = Depends(get_zareo_system)
):
    """Perform vehicle diagnostic scan."""
    try:
        if not await check_obd2_permission(current_user, "read_data"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="OBD2 read permission required"
            )
        
        if not zareo_system.is_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OBD2 system is not running"
            )
        
        diagnostic_result = await zareo_system.perform_vehicle_diagnostic()
        
        return {
            "success": True,
            "diagnostic_result": diagnostic_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Diagnostic scan failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Diagnostic scan failed"
        )

@router.post("/bidirectional/actuator-test")
async def perform_actuator_test(
    request: ActuatorTestRequest,
    current_user: User = Depends(get_current_admin_user),
    zareo_system: ZareoOBD2System = Depends(get_zareo_system)
):
    """Perform bidirectional actuator test (admin only)."""
    try:
        if not await check_obd2_permission(current_user, "bidirectional_access"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bidirectional access permission required"
            )
        
        if not zareo_system.scanner or zareo_system.scanner.mode != ScannerMode.BIDIRECTIONAL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bidirectional scanner not available or not in bidirectional mode"
            )
        
        result = await zareo_system.scanner.perform_actuator_test(
            request.actuator_name,
            request.parameters
        )
        
        return {
            "success": True,
            "test_result": result,
            "actuator": request.actuator_name,
            "parameters": request.parameters,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Actuator test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Actuator test failed"
        )

@router.post("/scanner/configure")
async def configure_scanner(
    request: ScannerConfigRequest,
    current_user: User = Depends(get_current_admin_user),
    zareo_system: ZareoOBD2System = Depends(get_zareo_system)
):
    """Configure scanner mode and settings (admin only)."""
    try:
        if not zareo_system.scanner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scanner not available"
            )
        
        # Validate scanner mode
        try:
            scanner_mode = ScannerMode(request.mode)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid scanner mode"
            )
        
        # Check permissions for bidirectional mode
        if scanner_mode == ScannerMode.BIDIRECTIONAL or request.enable_bidirectional:
            if not await check_obd2_permission(current_user, "bidirectional_access"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bidirectional access permission required"
                )
        
        # Configure scanner
        zareo_system.scanner.mode = scanner_mode
        
        return {
            "success": True,
            "scanner_mode": scanner_mode.value,
            "message": "Scanner configured successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scanner configuration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scanner configuration failed"
        )

@router.get("/sessions")
async def get_active_sessions(
    current_user: User = Depends(get_current_user)
):
    """Get list of active OBD2 sessions."""
    try:
        # Filter sessions based on user permissions
        filtered_sessions = {}
        
        for session_id, session_info in _active_sessions.items():
            # Users can see their own sessions, admins can see all
            if (session_info["user_id"] == current_user.id or 
                await check_obd2_permission(current_user, "audit_access")):
                filtered_sessions[session_id] = session_info
        
        return {
            "active_sessions": filtered_sessions,
            "total_sessions": len(filtered_sessions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sessions"
        )

@router.get("/data/live")
async def get_live_data(
    current_user: User = Depends(get_current_user),
    zareo_system: ZareoOBD2System = Depends(get_zareo_system)
):
    """Get current live OBD2 data."""
    try:
        if not await check_obd2_permission(current_user, "read_data"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="OBD2 read permission required"
            )
        
        if not zareo_system.obd2_manager or not zareo_system.is_running:
            return {
                "connected": False,
                "message": "OBD2 system not running"
            }
        
        # Get current parameter values
        live_data = {}
        common_parameters = ['RPM', 'SPEED', 'COOLANT_TEMP', 'INTAKE_TEMP', 'MAF', 'LOAD']
        
        for param in common_parameters:
            try:
                value = await zareo_system.obd2_manager.query_parameter(param)
                if value is not None:
                    live_data[param] = {
                        "value": str(value.value) if hasattr(value, 'value') else str(value),
                        "unit": str(value.unit) if hasattr(value, 'unit') else None,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            except Exception as param_error:
                logger.debug(f"Failed to get parameter {param}: {param_error}")
        
        return {
            "connected": True,
            "live_data": live_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get live data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get live data"
        )

@router.websocket("/ws/live-data")
async def websocket_live_data(websocket: WebSocket):
    """WebSocket endpoint for real-time OBD2 data streaming."""
    await websocket.accept()
    _websocket_connections.append(websocket)
    
    try:
        zareo_system = await get_zareo_system()
        
        while True:
            try:
                # Get live data
                if zareo_system.is_running and zareo_system.obd2_manager:
                    live_data = {}
                    common_parameters = ['RPM', 'SPEED', 'COOLANT_TEMP']
                    
                    for param in common_parameters:
                        try:
                            value = await zareo_system.obd2_manager.query_parameter(param)
                            if value is not None:
                                live_data[param] = {
                                    "value": str(value.value) if hasattr(value, 'value') else str(value),
                                    "unit": str(value.unit) if hasattr(value, 'unit') else None
                                }
                        except:
                            continue
                    
                    # Send data to client
                    await websocket.send_text(json.dumps({
                        "type": "live_data",
                        "data": live_data,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "connected": False,
                        "message": "OBD2 system not running"
                    }))
                
                # Wait before next update
                await asyncio.sleep(1.0)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal error occurred"
                }))
                await asyncio.sleep(5.0)
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _websocket_connections:
            _websocket_connections.remove(websocket)

# Utility function to broadcast to all connected WebSocket clients
async def broadcast_to_websockets(message: Dict[str, Any]):
    """Broadcast a message to all connected WebSocket clients."""
    if not _websocket_connections:
        return
    
    message_json = json.dumps(message)
    disconnected = []
    
    for websocket in _websocket_connections:
        try:
            await websocket.send_text(message_json)
        except:
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for websocket in disconnected:
        _websocket_connections.remove(websocket)