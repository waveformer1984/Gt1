#!/usr/bin/env python3
"""
Overwatch Task Handlers
=======================

Specialized task handlers for different subsystems and operations.
"""

import asyncio
import json
import logging
import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .overwatch import Task, TaskHandler, TaskResult, TaskStatus, TaskType

logger = logging.getLogger(__name__)


class OBD2DiagnosticHandler(TaskHandler):
    """Handler for OBD2 diagnostic tasks."""
    
    def __init__(self, obd2_manager=None):
        self.obd2_manager = obd2_manager
    
    async def execute(self, task: Task) -> TaskResult:
        """Execute OBD2 diagnostic task."""
        start_time = datetime.now()
        
        try:
            diagnostic_data = {
                "timestamp": start_time.isoformat(),
                "diagnostic_codes": [],
                "live_data": {},
                "connection_status": "unknown"
            }
            
            # If OBD2 manager is available, use it
            if self.obd2_manager:
                try:
                    # Get diagnostic trouble codes
                    dtcs = await self._get_diagnostic_codes()
                    diagnostic_data["diagnostic_codes"] = dtcs
                    
                    # Get live data
                    live_data = await self._get_live_data()
                    diagnostic_data["live_data"] = live_data
                    
                    diagnostic_data["connection_status"] = "connected"
                    
                except Exception as e:
                    diagnostic_data["connection_status"] = f"error: {str(e)}"
            else:
                # Simulate diagnostic data for testing
                diagnostic_data.update({
                    "connection_status": "simulated",
                    "diagnostic_codes": [
                        {"code": "P0301", "description": "Cylinder 1 Misfire Detected"},
                        {"code": "P0171", "description": "System Too Lean (Bank 1)"}
                    ],
                    "live_data": {
                        "engine_rpm": 750,
                        "vehicle_speed": 0,
                        "engine_load": 15.2,
                        "coolant_temp": 85,
                        "fuel_pressure": 58.5
                    }
                })
            
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result_data=diagnostic_data,
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
            
        except Exception as e:
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
    
    async def _get_diagnostic_codes(self) -> List[Dict[str, str]]:
        """Get diagnostic trouble codes from OBD2."""
        if self.obd2_manager and hasattr(self.obd2_manager, 'get_dtcs'):
            return await self.obd2_manager.get_dtcs()
        return []
    
    async def _get_live_data(self) -> Dict[str, Any]:
        """Get live data from OBD2."""
        if self.obd2_manager and hasattr(self.obd2_manager, 'get_live_data'):
            return await self.obd2_manager.get_live_data()
        return {}
    
    def can_handle(self, task: Task) -> bool:
        """Check if this handler can execute the given task."""
        return task.task_type == TaskType.OBD2_DIAGNOSTIC


class PerformanceCheckHandler(TaskHandler):
    """Handler for performance monitoring tasks."""
    
    async def execute(self, task: Task) -> TaskResult:
        """Execute performance check."""
        start_time = datetime.now()
        
        try:
            import psutil
            
            # Collect comprehensive performance data
            performance_data = {
                "timestamp": start_time.isoformat(),
                "cpu": self._get_cpu_metrics(),
                "memory": self._get_memory_metrics(),
                "disk": self._get_disk_metrics(),
                "network": self._get_network_metrics(),
                "processes": self._get_process_metrics()
            }
            
            # Calculate performance score
            score = self._calculate_performance_score(performance_data)
            performance_data["performance_score"] = score
            
            # Determine status
            status = "good"
            if score < 70:
                status = "warning"
            if score < 50:
                status = "critical"
            
            performance_data["status"] = status
            
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result_data=performance_data,
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
            
        except Exception as e:
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
    
    def _get_cpu_metrics(self) -> Dict[str, Any]:
        """Get CPU performance metrics."""
        import psutil
        
        return {
            "usage_percent": psutil.cpu_percent(interval=1),
            "core_count": psutil.cpu_count(),
            "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    
    def _get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory performance metrics."""
        import psutil
        
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "virtual": memory._asdict(),
            "swap": swap._asdict(),
            "usage_percent": memory.percent
        }
    
    def _get_disk_metrics(self) -> Dict[str, Any]:
        """Get disk performance metrics."""
        import psutil
        
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        return {
            "usage": disk_usage._asdict(),
            "io_counters": disk_io._asdict() if disk_io else None,
            "usage_percent": (disk_usage.used / disk_usage.total) * 100
        }
    
    def _get_network_metrics(self) -> Dict[str, Any]:
        """Get network performance metrics."""
        import psutil
        
        network_io = psutil.net_io_counters()
        connections = len(psutil.net_connections())
        
        return {
            "io_counters": network_io._asdict() if network_io else None,
            "active_connections": connections
        }
    
    def _get_process_metrics(self) -> Dict[str, Any]:
        """Get process performance metrics."""
        import psutil
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage and take top 10
        top_processes = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]
        
        return {
            "total_count": len(processes),
            "top_cpu_consumers": top_processes
        }
    
    def _calculate_performance_score(self, data: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)."""
        scores = []
        
        # CPU score (lower usage = higher score)
        cpu_usage = data["cpu"]["usage_percent"]
        cpu_score = max(0, 100 - cpu_usage)
        scores.append(cpu_score)
        
        # Memory score
        memory_usage = data["memory"]["usage_percent"]
        memory_score = max(0, 100 - memory_usage)
        scores.append(memory_score)
        
        # Disk score
        disk_usage = data["disk"]["usage_percent"]
        disk_score = max(0, 100 - disk_usage)
        scores.append(disk_score)
        
        # Return weighted average
        return sum(scores) / len(scores)
    
    def can_handle(self, task: Task) -> bool:
        """Check if this handler can execute the given task."""
        return task.task_type == TaskType.PERFORMANCE_CHECK


class DataBackupHandler(TaskHandler):
    """Handler for data backup tasks."""
    
    def __init__(self, backup_directory: str = "/tmp/overwatch_backups"):
        self.backup_directory = Path(backup_directory)
        self.backup_directory.mkdir(parents=True, exist_ok=True)
    
    async def execute(self, task: Task) -> TaskResult:
        """Execute data backup task."""
        start_time = datetime.now()
        
        try:
            backup_data = {
                "timestamp": start_time.isoformat(),
                "backup_directory": str(self.backup_directory),
                "backed_up_items": [],
                "total_size": 0,
                "status": "in_progress"
            }
            
            # Create timestamped backup folder
            backup_timestamp = start_time.strftime("%Y%m%d_%H%M%S")
            backup_folder = self.backup_directory / f"backup_{backup_timestamp}"
            backup_folder.mkdir(exist_ok=True)
            
            # Backup configurations
            config_backup = await self._backup_configurations(backup_folder)
            backup_data["backed_up_items"].extend(config_backup)
            
            # Backup databases
            db_backup = await self._backup_databases(backup_folder)
            backup_data["backed_up_items"].extend(db_backup)
            
            # Backup logs
            log_backup = await self._backup_logs(backup_folder)
            backup_data["backed_up_items"].extend(log_backup)
            
            # Calculate total backup size
            total_size = sum(item.get("size", 0) for item in backup_data["backed_up_items"])
            backup_data["total_size"] = total_size
            backup_data["status"] = "completed"
            backup_data["backup_path"] = str(backup_folder)
            
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result_data=backup_data,
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
            
        except Exception as e:
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
    
    async def _backup_configurations(self, backup_folder: Path) -> List[Dict[str, Any]]:
        """Backup configuration files."""
        backed_up = []
        config_folder = backup_folder / "configs"
        config_folder.mkdir(exist_ok=True)
        
        # Look for common config files
        config_patterns = [
            "*.yaml", "*.yml", "*.json", "*.toml", "*.ini", "*.conf", "*.cfg"
        ]
        
        for pattern in config_patterns:
            for config_file in Path("/workspace").rglob(pattern):
                if config_file.is_file() and config_file.stat().st_size < 10 * 1024 * 1024:  # Skip files > 10MB
                    try:
                        dest = config_folder / config_file.name
                        shutil.copy2(config_file, dest)
                        
                        backed_up.append({
                            "type": "config",
                            "source": str(config_file),
                            "destination": str(dest),
                            "size": config_file.stat().st_size
                        })
                    except Exception as e:
                        logger.warning(f"Failed to backup config {config_file}: {e}")
        
        return backed_up
    
    async def _backup_databases(self, backup_folder: Path) -> List[Dict[str, Any]]:
        """Backup database files."""
        backed_up = []
        db_folder = backup_folder / "databases"
        db_folder.mkdir(exist_ok=True)
        
        # Look for SQLite databases
        for db_file in Path("/workspace").rglob("*.db"):
            if db_file.is_file():
                try:
                    dest = db_folder / db_file.name
                    shutil.copy2(db_file, dest)
                    
                    backed_up.append({
                        "type": "database",
                        "source": str(db_file),
                        "destination": str(dest),
                        "size": db_file.stat().st_size
                    })
                except Exception as e:
                    logger.warning(f"Failed to backup database {db_file}: {e}")
        
        return backed_up
    
    async def _backup_logs(self, backup_folder: Path) -> List[Dict[str, Any]]:
        """Backup recent log files."""
        backed_up = []
        log_folder = backup_folder / "logs"
        log_folder.mkdir(exist_ok=True)
        
        # Look for log files in logs directory
        logs_dir = Path("/workspace/logs")
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                if log_file.is_file():
                    try:
                        dest = log_folder / log_file.name
                        shutil.copy2(log_file, dest)
                        
                        backed_up.append({
                            "type": "log",
                            "source": str(log_file),
                            "destination": str(dest),
                            "size": log_file.stat().st_size
                        })
                    except Exception as e:
                        logger.warning(f"Failed to backup log {log_file}: {e}")
        
        return backed_up
    
    def can_handle(self, task: Task) -> bool:
        """Check if this handler can execute the given task."""
        return task.task_type == TaskType.DATA_BACKUP


class MaintenanceHandler(TaskHandler):
    """Handler for system maintenance tasks."""
    
    async def execute(self, task: Task) -> TaskResult:
        """Execute maintenance task."""
        start_time = datetime.now()
        
        try:
            maintenance_data = {
                "timestamp": start_time.isoformat(),
                "maintenance_tasks": [],
                "status": "in_progress"
            }
            
            # Clean temporary files
            temp_cleanup = await self._cleanup_temp_files()
            maintenance_data["maintenance_tasks"].append(temp_cleanup)
            
            # Clean old log files
            log_cleanup = await self._cleanup_old_logs()
            maintenance_data["maintenance_tasks"].append(log_cleanup)
            
            # Optimize databases
            db_optimization = await self._optimize_databases()
            maintenance_data["maintenance_tasks"].append(db_optimization)
            
            # Check disk space
            disk_check = await self._check_disk_space()
            maintenance_data["maintenance_tasks"].append(disk_check)
            
            maintenance_data["status"] = "completed"
            
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result_data=maintenance_data,
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
            
        except Exception as e:
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
    
    async def _cleanup_temp_files(self) -> Dict[str, Any]:
        """Clean up temporary files."""
        cleaned_size = 0
        cleaned_count = 0
        
        try:
            # Clean __pycache__ directories
            for pycache_dir in Path("/workspace").rglob("__pycache__"):
                if pycache_dir.is_dir():
                    for pyc_file in pycache_dir.glob("*.pyc"):
                        try:
                            cleaned_size += pyc_file.stat().st_size
                            pyc_file.unlink()
                            cleaned_count += 1
                        except Exception:
                            pass
            
            # Clean .tmp files
            for tmp_file in Path("/workspace").rglob("*.tmp"):
                if tmp_file.is_file():
                    try:
                        cleaned_size += tmp_file.stat().st_size
                        tmp_file.unlink()
                        cleaned_count += 1
                    except Exception:
                        pass
        
        except Exception as e:
            return {
                "task": "temp_cleanup",
                "status": "failed",
                "error": str(e)
            }
        
        return {
            "task": "temp_cleanup",
            "status": "completed",
            "files_cleaned": cleaned_count,
            "space_freed": cleaned_size
        }
    
    async def _cleanup_old_logs(self) -> Dict[str, Any]:
        """Clean up old log files."""
        cleaned_size = 0
        cleaned_count = 0
        
        try:
            logs_dir = Path("/workspace/logs")
            if logs_dir.exists():
                # Keep only last 30 days of logs
                cutoff_time = datetime.now().timestamp() - (30 * 24 * 60 * 60)
                
                for log_file in logs_dir.glob("*.log"):
                    if log_file.is_file() and log_file.stat().st_mtime < cutoff_time:
                        try:
                            cleaned_size += log_file.stat().st_size
                            log_file.unlink()
                            cleaned_count += 1
                        except Exception:
                            pass
        
        except Exception as e:
            return {
                "task": "log_cleanup",
                "status": "failed",
                "error": str(e)
            }
        
        return {
            "task": "log_cleanup",
            "status": "completed",
            "files_cleaned": cleaned_count,
            "space_freed": cleaned_size
        }
    
    async def _optimize_databases(self) -> Dict[str, Any]:
        """Optimize database files."""
        optimized_count = 0
        
        try:
            for db_file in Path("/workspace").rglob("*.db"):
                if db_file.is_file():
                    try:
                        # Run VACUUM on SQLite databases
                        conn = sqlite3.connect(str(db_file))
                        conn.execute("VACUUM")
                        conn.close()
                        optimized_count += 1
                    except Exception:
                        pass
        
        except Exception as e:
            return {
                "task": "database_optimization",
                "status": "failed",
                "error": str(e)
            }
        
        return {
            "task": "database_optimization",
            "status": "completed",
            "databases_optimized": optimized_count
        }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            import psutil
            
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            status = "ok"
            if free_percent < 20:
                status = "warning"
            if free_percent < 10:
                status = "critical"
            
            return {
                "task": "disk_space_check",
                "status": "completed",
                "free_space_gb": disk_usage.free / (1024**3),
                "free_space_percent": free_percent,
                "disk_status": status
            }
        
        except Exception as e:
            return {
                "task": "disk_space_check",
                "status": "failed",
                "error": str(e)
            }
    
    def can_handle(self, task: Task) -> bool:
        """Check if this handler can execute the given task."""
        return task.task_type == TaskType.MAINTENANCE


class SecurityScanHandler(TaskHandler):
    """Handler for security scan tasks."""
    
    async def execute(self, task: Task) -> TaskResult:
        """Execute security scan task."""
        start_time = datetime.now()
        
        try:
            security_data = {
                "timestamp": start_time.isoformat(),
                "scan_results": [],
                "security_score": 0,
                "vulnerabilities": [],
                "status": "in_progress"
            }
            
            # Check file permissions
            permission_check = await self._check_file_permissions()
            security_data["scan_results"].append(permission_check)
            
            # Check for sensitive files
            sensitive_check = await self._check_sensitive_files()
            security_data["scan_results"].append(sensitive_check)
            
            # Check running processes
            process_check = await self._check_running_processes()
            security_data["scan_results"].append(process_check)
            
            # Calculate security score
            score = self._calculate_security_score(security_data["scan_results"])
            security_data["security_score"] = score
            
            # Collect vulnerabilities
            vulnerabilities = []
            for result in security_data["scan_results"]:
                vulnerabilities.extend(result.get("vulnerabilities", []))
            security_data["vulnerabilities"] = vulnerabilities
            
            security_data["status"] = "completed"
            
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result_data=security_data,
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
            
        except Exception as e:
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
    
    async def _check_file_permissions(self) -> Dict[str, Any]:
        """Check file permissions for security issues."""
        vulnerabilities = []
        
        try:
            # Check for world-writable files
            for file_path in Path("/workspace").rglob("*"):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        # Check if world-writable (others have write permission)
                        if stat.st_mode & 0o002:
                            vulnerabilities.append({
                                "type": "world_writable_file",
                                "path": str(file_path),
                                "severity": "medium"
                            })
                    except Exception:
                        pass
        
        except Exception as e:
            return {
                "check": "file_permissions",
                "status": "failed",
                "error": str(e)
            }
        
        return {
            "check": "file_permissions",
            "status": "completed",
            "vulnerabilities": vulnerabilities,
            "files_checked": len(list(Path("/workspace").rglob("*")))
        }
    
    async def _check_sensitive_files(self) -> Dict[str, Any]:
        """Check for sensitive files that shouldn't be exposed."""
        vulnerabilities = []
        
        sensitive_patterns = [
            "*.key", "*.pem", "*.p12", "*.pfx",
            ".env", ".env.*", "*.secrets", "password*",
            "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"
        ]
        
        try:
            for pattern in sensitive_patterns:
                for file_path in Path("/workspace").rglob(pattern):
                    if file_path.is_file():
                        vulnerabilities.append({
                            "type": "sensitive_file_exposed",
                            "path": str(file_path),
                            "pattern": pattern,
                            "severity": "high"
                        })
        
        except Exception as e:
            return {
                "check": "sensitive_files",
                "status": "failed",
                "error": str(e)
            }
        
        return {
            "check": "sensitive_files",
            "status": "completed",
            "vulnerabilities": vulnerabilities
        }
    
    async def _check_running_processes(self) -> Dict[str, Any]:
        """Check running processes for security concerns."""
        vulnerabilities = []
        
        try:
            import psutil
            
            # Check for processes running as root that shouldn't
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    if proc.info['username'] == 'root':
                        # Flag common services that shouldn't run as root
                        risky_processes = ['nginx', 'apache2', 'httpd', 'node', 'python']
                        if any(risky in proc.info['name'].lower() for risky in risky_processes):
                            vulnerabilities.append({
                                "type": "process_running_as_root",
                                "process": proc.info['name'],
                                "pid": proc.info['pid'],
                                "severity": "medium"
                            })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        
        except Exception as e:
            return {
                "check": "running_processes",
                "status": "failed",
                "error": str(e)
            }
        
        return {
            "check": "running_processes",
            "status": "completed",
            "vulnerabilities": vulnerabilities
        }
    
    def _calculate_security_score(self, scan_results: List[Dict[str, Any]]) -> float:
        """Calculate security score based on scan results."""
        total_vulnerabilities = 0
        high_severity = 0
        medium_severity = 0
        
        for result in scan_results:
            vulnerabilities = result.get("vulnerabilities", [])
            total_vulnerabilities += len(vulnerabilities)
            
            for vuln in vulnerabilities:
                if vuln.get("severity") == "high":
                    high_severity += 1
                elif vuln.get("severity") == "medium":
                    medium_severity += 1
        
        # Calculate score (100 = perfect, 0 = many issues)
        score = 100
        score -= high_severity * 20  # High severity issues cost 20 points each
        score -= medium_severity * 10  # Medium severity issues cost 10 points each
        
        return max(0, score)
    
    def can_handle(self, task: Task) -> bool:
        """Check if this handler can execute the given task."""
        return task.task_type == TaskType.SECURITY_SCAN


# Registry of all available handlers
AVAILABLE_HANDLERS = {
    TaskType.OBD2_DIAGNOSTIC: OBD2DiagnosticHandler,
    TaskType.PERFORMANCE_CHECK: PerformanceCheckHandler,
    TaskType.DATA_BACKUP: DataBackupHandler,
    TaskType.MAINTENANCE: MaintenanceHandler,
    TaskType.SECURITY_SCAN: SecurityScanHandler
}


def register_all_handlers(overwatch_system):
    """Register all available handlers with the overwatch system."""
    for task_type, handler_class in AVAILABLE_HANDLERS.items():
        handler = handler_class()
        overwatch_system.register_task_handler(task_type, handler)
        logger.info(f"Registered {handler_class.__name__} for {task_type}")