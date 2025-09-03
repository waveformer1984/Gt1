"""
System-Wide Integrated Device Dashboard (SIDD)
Unified control center for ballsDeepnit + Hydi + Frank ecosystem
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..monitoring.performance import performance_monitor, get_memory_usage
from ..utils.logging import get_logger
from ..core.config import settings
from .hardware_monitor import frank_hardware


logger = get_logger(__name__)


class DeviceMonitor:
    """Monitor individual devices and services"""
    
    def __init__(self):
        self.devices = {}
        self.services = {}
        
    async def discover_local_device(self) -> Dict[str, Any]:
        """Discover and monitor the local device"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            device_info = {
                "id": "localhost",
                "name": "Local System",
                "type": "computer",
                "status": "online",
                "last_seen": datetime.now().isoformat(),
                "boot_time": boot_time.isoformat(),
                "platform": psutil.platform,
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "disk_total": psutil.disk_usage('/').total if psutil.disk_usage('/') else 0
            }
            
            return device_info
            
        except Exception as e:
            logger.error(f"Failed to discover local device: {e}")
            return {"id": "localhost", "status": "error", "error": str(e)}
    
    async def get_device_metrics(self, device_id: str) -> Dict[str, Any]:
        """Get real-time metrics for a device"""
        if device_id == "localhost":
            return await self._get_local_metrics()
        return {}
    
    async def _get_local_metrics(self) -> Dict[str, Any]:
        """Get local system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent()  # Non-blocking call after initial setup
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            return {
                "timestamp": time.time(),
                "cpu": {
                    "percent": cpu_percent,
                    "frequency": cpu_freq.current if cpu_freq else 0,
                    "cores": self.cpu_count
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "percent": swap.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100 if disk.total > 0 else 0
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "processes": process_count,
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
            
        except Exception as e:
            logger.error(f"Failed to get local metrics: {e}")
            return {"error": str(e), "timestamp": time.time()}


class ServiceMonitor:
    """Monitor ballsDeepnit, Frank, and Hydi services"""
    
    def __init__(self):
        self.services = {
            "ballsdeepnit": {"name": "ballsDeepnit Framework", "status": "unknown"},
            "frank": {"name": "Frank Bot AI", "status": "unknown"},
            "hydi": {"name": "Hydi REPL", "status": "unknown"}
        }
    
    async def check_ballsdeepnit_status(self) -> Dict[str, Any]:
        """Check ballsDeepnit framework status"""
        try:
            # Check if performance monitoring is active
            perf_status = performance_monitor.get_status() if hasattr(performance_monitor, 'get_status') else {}
            
            memory_usage = get_memory_usage()
            
            return {
                "status": "running",
                "health": "healthy",
                "memory_usage": memory_usage,
                "performance": perf_status,
                "version": getattr(settings, "VERSION", "unknown"),
                "uptime": time.time()  # Simplified
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_frank_status(self) -> Dict[str, Any]:
        """Check Frank Bot status"""
        try:
            frank_pid_file = Path("frank_standalone/frank.pid")
            
            if frank_pid_file.exists():
                pid = int(frank_pid_file.read_text().strip())
                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    return {
                        "status": "running",
                        "health": "healthy",
                        "pid": pid,
                        "memory": process.memory_info().rss,
                        "cpu": process.cpu_percent()
                    }
                else:
                    return {"status": "stopped", "reason": "Process not found"}
            else:
                return {"status": "not_installed", "reason": "PID file not found"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_hydi_status(self) -> Dict[str, Any]:
        """Check Hydi REPL status"""
        try:
            # Look for Java processes running REPL
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'java' and proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'CommandREPL' in cmdline:
                            return {
                                "status": "running",
                                "health": "healthy",
                                "pid": proc.info['pid'],
                                "memory": proc.memory_info().rss,
                                "cpu": proc.cpu_percent()
                            }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {"status": "stopped", "reason": "REPL process not found"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_all_service_status(self) -> Dict[str, Any]:
        """Get status of all monitored services"""
        return {
            "ballsdeepnit": await self.check_ballsdeepnit_status(),
            "frank": await self.check_frank_status(),
            "hydi": await self.check_hydi_status()
        }


class SIDDDashboard:
    """Main SIDD Dashboard controller"""
    
    def __init__(self):
        self.device_monitor = DeviceMonitor()
        self.service_monitor = ServiceMonitor()
        self.connected_clients = set()
        
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data"""
        try:
            # Get device info and metrics
            local_device = await self.device_monitor.discover_local_device()
            device_metrics = await self.device_monitor.get_device_metrics("localhost")
            
            # Get service status
            services = await self.service_monitor.get_all_service_status()
            
            # Get Frank's hardware specifications
            hardware_specs = await frank_hardware.get_complete_hardware_specs()
            
            # Calculate overall health
            health_score = self._calculate_health_score(device_metrics, services)
            
            return {
                "timestamp": time.time(),
                "devices": {
                    "localhost": {
                        **local_device,
                        "metrics": device_metrics
                    }
                },
                "services": services,
                "hardware": hardware_specs,
                "health": {
                    "score": health_score,
                    "status": self._get_health_status(health_score),
                    "alerts": self._get_alerts(device_metrics, services)
                },
                "system": {
                    "ballsdeepnit_version": settings.VERSION,
                    "dashboard_version": "1.0.0",
                    "uptime": time.time()  # Simplified
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e), "timestamp": time.time()}
    
    def _calculate_health_score(self, metrics: Dict[str, Any], services: Dict[str, Any]) -> float:
        """Calculate overall system health score (0-100)"""
        try:
            score = 100.0
            
            # Penalize based on resource usage
            if 'cpu' in metrics and metrics['cpu'].get('percent', 0) > 80:
                score -= 20
            if 'memory' in metrics and metrics['memory'].get('percent', 0) > 85:
                score -= 20
            if 'disk' in metrics and metrics['disk'].get('percent', 0) > 90:
                score -= 15
            
            # Penalize for service issues
            for service_name, service_data in services.items():
                if service_data.get('status') != 'running':
                    score -= 15
            
            return max(0.0, score)
            
        except Exception:
            return 50.0  # Default moderate health
    
    def _get_health_status(self, score: float) -> str:
        """Convert health score to status string"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good" 
        elif score >= 50:
            return "fair"
        else:
            return "poor"
    
    def _get_alerts(self, metrics: Dict[str, Any], services: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate system alerts"""
        alerts = []
        
        try:
            # Resource alerts
            if 'cpu' in metrics and metrics['cpu'].get('percent', 0) > 80:
                alerts.append({
                    "type": "warning",
                    "message": f"High CPU usage: {metrics['cpu']['percent']:.1f}%",
                    "component": "cpu"
                })
            
            if 'memory' in metrics and metrics['memory'].get('percent', 0) > 85:
                alerts.append({
                    "type": "warning", 
                    "message": f"High memory usage: {metrics['memory']['percent']:.1f}%",
                    "component": "memory"
                })
            
            if 'disk' in metrics and metrics['disk'].get('percent', 0) > 90:
                alerts.append({
                    "type": "critical",
                    "message": f"Low disk space: {metrics['disk']['percent']:.1f}% used",
                    "component": "disk"
                })
            
            # Service alerts
            for service_name, service_data in services.items():
                if service_data.get('status') == 'error':
                    alerts.append({
                        "type": "error",
                        "message": f"{service_name} service error: {service_data.get('error', 'Unknown')}",
                        "component": service_name
                    })
                elif service_data.get('status') == 'stopped':
                    alerts.append({
                        "type": "info",
                        "message": f"{service_name} service is stopped",
                        "component": service_name
                    })
        
        except Exception as e:
            logger.error(f"Failed to generate alerts: {e}")
        
        return alerts


# Global dashboard instance
dashboard = SIDDDashboard()