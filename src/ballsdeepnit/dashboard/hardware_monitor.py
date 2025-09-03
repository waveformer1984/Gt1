"""
Frank Hardware Monitoring System
Comprehensive hardware specification detection and monitoring for Frank's upgrades
"""

import subprocess
import psutil
import platform
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..utils.logging import get_logger

logger = get_logger(__name__)


class FrankHardwareMonitor:
    """Monitor Frank's hardware specifications and upgrades"""
    
    def __init__(self):
        self.hardware_cache = {}
        self.last_scan = None
        
    async def get_complete_hardware_specs(self) -> Dict[str, Any]:
        """Get comprehensive hardware specifications for Frank"""
        try:
            specs = {
                "timestamp": datetime.now().isoformat(),
                "system_info": await self._get_system_info(),
                "cpu_specs": await self._get_cpu_specifications(),
                "memory_specs": await self._get_memory_specifications(),
                "storage_specs": await self._get_storage_specifications(),
                "network_specs": await self._get_network_specifications(),
                "gpu_specs": await self._get_gpu_specifications(),
                "motherboard_specs": await self._get_motherboard_specs(),
                "power_specs": await self._get_power_specifications(),
                "thermal_specs": await self._get_thermal_specifications(),
                "upgrade_analysis": await self._analyze_hardware_upgrades()
            }
            
            self.hardware_cache = specs
            self.last_scan = datetime.now()
            
            return specs
            
        except Exception as e:
            logger.error(f"Failed to get hardware specifications: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            return {
                "hostname": platform.node(),
                "platform": platform.platform(),
                "architecture": platform.architecture()[0],
                "machine": platform.machine(),
                "processor": platform.processor(),
                "kernel": platform.release(),
                "os_version": platform.version(),
                "boot_time": boot_time.isoformat(),
                "uptime_days": uptime.days,
                "uptime_hours": uptime.seconds // 3600,
                "python_version": platform.python_version()
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"error": str(e)}
    
    async def _get_cpu_specifications(self) -> Dict[str, Any]:
        """Get detailed CPU specifications"""
        try:
            cpu_info = {
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "current_usage": psutil.cpu_percent(interval=1),
                "per_core_usage": psutil.cpu_percent(percpu=True, interval=1)
            }
            
            # Get CPU frequency
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                cpu_info.update({
                    "current_frequency_mhz": round(cpu_freq.current, 2),
                    "min_frequency_mhz": round(cpu_freq.min, 2) if cpu_freq.min else "N/A",
                    "max_frequency_mhz": round(cpu_freq.max, 2) if cpu_freq.max else "N/A"
                })
            
            # Get CPU model from /proc/cpuinfo
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    
                    # Extract CPU model
                    for line in cpuinfo.split('\n'):
                        if 'model name' in line:
                            cpu_info['model'] = line.split(':')[1].strip()
                            break
                    
                    # Extract cache sizes
                    cache_size = re.search(r'cache size\s*:\s*([^\n]*)', cpuinfo)
                    if cache_size:
                        cpu_info['cache_size'] = cache_size.group(1).strip()
                    
                    # Extract CPU flags
                    flags = re.search(r'flags\s*:\s*([^\n]*)', cpuinfo)
                    if flags:
                        cpu_info['features'] = flags.group(1).strip().split()[:20]  # First 20 features
                        
            except Exception as e:
                logger.warning(f"Could not read CPU info from /proc/cpuinfo: {e}")
            
            # Get load averages
            if hasattr(psutil, 'getloadavg'):
                load_avg = psutil.getloadavg()
                cpu_info['load_average'] = {
                    "1_min": round(load_avg[0], 2),
                    "5_min": round(load_avg[1], 2),
                    "15_min": round(load_avg[2], 2)
                }
            
            return cpu_info
            
        except Exception as e:
            logger.error(f"Failed to get CPU specifications: {e}")
            return {"error": str(e)}
    
    async def _get_memory_specifications(self) -> Dict[str, Any]:
        """Get detailed memory specifications"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            memory_info = {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "free_gb": round(memory.free / (1024**3), 2),
                "cached_gb": round(memory.cached / (1024**3), 2) if hasattr(memory, 'cached') else 0,
                "buffers_gb": round(memory.buffers / (1024**3), 2) if hasattr(memory, 'buffers') else 0,
                "usage_percent": memory.percent,
                "swap_total_gb": round(swap.total / (1024**3), 2),
                "swap_used_gb": round(swap.used / (1024**3), 2),
                "swap_free_gb": round(swap.free / (1024**3), 2),
                "swap_percent": swap.percent
            }
            
            # Get detailed memory info from /proc/meminfo
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    
                    # Extract specific memory metrics
                    memory_details = {}
                    for line in meminfo.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            if 'kB' in value:
                                # Convert to GB
                                kb_value = int(value.replace('kB', '').strip())
                                memory_details[key.strip()] = round(kb_value / (1024**2), 2)
                    
                    memory_info['detailed_breakdown'] = memory_details
                    
            except Exception as e:
                logger.warning(f"Could not read detailed memory info: {e}")
            
            return memory_info
            
        except Exception as e:
            logger.error(f"Failed to get memory specifications: {e}")
            return {"error": str(e)}
    
    async def _get_storage_specifications(self) -> Dict[str, Any]:
        """Get detailed storage specifications"""
        try:
            storage_info = {
                "disks": [],
                "partitions": [],
                "total_capacity_gb": 0,
                "total_used_gb": 0,
                "total_free_gb": 0
            }
            
            # Get disk usage for all partitions
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    partition_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "filesystem": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "usage_percent": round((usage.used / usage.total) * 100, 2)
                    }
                    
                    storage_info["partitions"].append(partition_info)
                    
                    # Accumulate totals (avoid duplicates by checking root mounts)
                    if partition.mountpoint == '/':
                        storage_info["total_capacity_gb"] += partition_info["total_gb"]
                        storage_info["total_used_gb"] += partition_info["used_gb"]
                        storage_info["total_free_gb"] += partition_info["free_gb"]
                        
                except (PermissionError, FileNotFoundError):
                    continue
            
            # Get disk I/O statistics
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    storage_info["io_stats"] = {
                        "read_count": disk_io.read_count,
                        "write_count": disk_io.write_count,
                        "read_bytes": disk_io.read_bytes,
                        "write_bytes": disk_io.write_bytes,
                        "read_time": disk_io.read_time,
                        "write_time": disk_io.write_time
                    }
            except Exception as e:
                logger.warning(f"Could not get disk I/O stats: {e}")
            
            return storage_info
            
        except Exception as e:
            logger.error(f"Failed to get storage specifications: {e}")
            return {"error": str(e)}
    
    async def _get_network_specifications(self) -> Dict[str, Any]:
        """Get network interface specifications"""
        try:
            network_info = {
                "interfaces": [],
                "io_stats": {},
                "connections": psutil.net_connections().__len__()
            }
            
            # Get network interfaces
            for interface_name, addresses in psutil.net_if_addrs().items():
                interface_info = {
                    "name": interface_name,
                    "addresses": []
                }
                
                for addr in addresses:
                    addr_info = {
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast
                    }
                    interface_info["addresses"].append(addr_info)
                
                # Get interface statistics
                try:
                    stats = psutil.net_if_stats()[interface_name]
                    interface_info["stats"] = {
                        "isup": stats.isup,
                        "duplex": str(stats.duplex),
                        "speed": stats.speed,
                        "mtu": stats.mtu
                    }
                except KeyError:
                    pass
                
                network_info["interfaces"].append(interface_info)
            
            # Get network I/O statistics
            net_io = psutil.net_io_counters()
            if net_io:
                network_info["io_stats"] = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "errin": net_io.errin,
                    "errout": net_io.errout,
                    "dropin": net_io.dropin,
                    "dropout": net_io.dropout
                }
            
            return network_info
            
        except Exception as e:
            logger.error(f"Failed to get network specifications: {e}")
            return {"error": str(e)}
    
    async def _get_gpu_specifications(self) -> Dict[str, Any]:
        """Get GPU specifications"""
        try:
            gpu_info = {
                "devices": [],
                "display_info": "Not available"
            }
            
            # Try to get GPU info via lspci
            try:
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if any(keyword in line.lower() for keyword in ['vga', 'display', '3d', 'graphics']):
                            gpu_info["devices"].append(line.strip())
                            
            except (subprocess.TimeoutExpired, FileNotFoundError):
                gpu_info["devices"] = ["GPU detection not available"]
            
            # Try to get additional GPU info
            try:
                # Check for nvidia-smi
                result = subprocess.run(['nvidia-smi', '-q'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    gpu_info["nvidia_details"] = "NVIDIA GPU detected"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            return gpu_info
            
        except Exception as e:
            logger.error(f"Failed to get GPU specifications: {e}")
            return {"error": str(e)}
    
    async def _get_motherboard_specs(self) -> Dict[str, Any]:
        """Get motherboard and system specifications"""
        try:
            mb_info = {
                "system_vendor": "Unknown",
                "system_model": "Unknown",
                "bios_info": "Unknown"
            }
            
            # Try to get DMI info
            try:
                # System vendor
                result = subprocess.run(['dmidecode', '-s', 'system-manufacturer'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    mb_info["system_vendor"] = result.stdout.strip()
                    
                # System model
                result = subprocess.run(['dmidecode', '-s', 'system-product-name'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    mb_info["system_model"] = result.stdout.strip()
                    
                # BIOS version
                result = subprocess.run(['dmidecode', '-s', 'bios-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    mb_info["bios_version"] = result.stdout.strip()
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                mb_info["note"] = "DMI information requires root access"
            
            return mb_info
            
        except Exception as e:
            logger.error(f"Failed to get motherboard specifications: {e}")
            return {"error": str(e)}
    
    async def _get_power_specifications(self) -> Dict[str, Any]:
        """Get power and battery specifications"""
        try:
            power_info = {
                "battery_present": False,
                "power_adapter": "Unknown"
            }
            
            # Check for battery
            try:
                battery = psutil.sensors_battery()
                if battery:
                    power_info.update({
                        "battery_present": True,
                        "battery_percent": battery.percent,
                        "power_plugged": battery.power_plugged,
                        "battery_time_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Unlimited"
                    })
            except Exception:
                power_info["battery_present"] = False
            
            return power_info
            
        except Exception as e:
            logger.error(f"Failed to get power specifications: {e}")
            return {"error": str(e)}
    
    async def _get_thermal_specifications(self) -> Dict[str, Any]:
        """Get thermal and temperature specifications"""
        try:
            thermal_info = {
                "temperatures": {},
                "fans": {}
            }
            
            # Get temperature sensors
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        thermal_info["temperatures"][name] = []
                        for entry in entries:
                            thermal_info["temperatures"][name].append({
                                "label": entry.label or "N/A",
                                "current": entry.current,
                                "high": entry.high,
                                "critical": entry.critical
                            })
            except Exception:
                thermal_info["temperatures"] = {"note": "Temperature sensors not available"}
            
            # Get fan information
            try:
                fans = psutil.sensors_fans()
                if fans:
                    for name, entries in fans.items():
                        thermal_info["fans"][name] = []
                        for entry in entries:
                            thermal_info["fans"][name].append({
                                "label": entry.label or "N/A",
                                "current": entry.current
                            })
            except Exception:
                thermal_info["fans"] = {"note": "Fan sensors not available"}
            
            return thermal_info
            
        except Exception as e:
            logger.error(f"Failed to get thermal specifications: {e}")
            return {"error": str(e)}
    
    async def _analyze_hardware_upgrades(self) -> Dict[str, Any]:
        """Analyze hardware for potential upgrades and bottlenecks"""
        try:
            analysis = {
                "upgrade_recommendations": [],
                "performance_bottlenecks": [],
                "hardware_score": 0,
                "upgrade_priorities": [],
                "upgrade_status": await self._check_upgrade_status(),
                "external_devices": await self._scan_external_devices()
            }
            
            # Analyze memory
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            
            if memory_gb < 8:
                analysis["upgrade_recommendations"].append({
                    "component": "Memory",
                    "current": f"{memory_gb:.1f}GB",
                    "recommended": "16GB+",
                    "priority": "High",
                    "reason": "Low memory capacity may cause performance issues"
                })
            elif memory.percent > 80:
                analysis["performance_bottlenecks"].append({
                    "component": "Memory",
                    "issue": f"High memory usage: {memory.percent}%",
                    "impact": "Performance degradation"
                })
            
            # Analyze CPU
            cpu_usage = psutil.cpu_percent(interval=1)
            if cpu_usage > 80:
                analysis["performance_bottlenecks"].append({
                    "component": "CPU",
                    "issue": f"High CPU usage: {cpu_usage}%",
                    "impact": "System responsiveness"
                })
            
            # Analyze disk space
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    usage_percent = (usage.used / usage.total) * 100
                    
                    if usage_percent > 90:
                        analysis["performance_bottlenecks"].append({
                            "component": "Storage",
                            "issue": f"Low disk space: {usage_percent:.1f}% used",
                            "impact": "System stability"
                        })
                    elif usage.total < 500 * (1024**3):  # Less than 500GB
                        analysis["upgrade_recommendations"].append({
                            "component": "Storage",
                            "current": f"{usage.total / (1024**3):.0f}GB",
                            "recommended": "1TB+ SSD",
                            "priority": "Medium",
                            "reason": "More storage capacity recommended"
                        })
                except:
                    continue
            
            # Calculate hardware score
            score = 100
            score -= len(analysis["performance_bottlenecks"]) * 15
            score -= len(analysis["upgrade_recommendations"]) * 10
            analysis["hardware_score"] = max(0, score)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze hardware upgrades: {e}")
            return {"error": str(e)}
    
    async def _check_upgrade_status(self) -> Dict[str, Any]:
        """Check for hardware upgrade status"""
        try:
            upgrade_status = {
                "ram_upgrade": {
                    "detected": False,
                    "capacity_gb": 0,
                    "status": "Unknown"
                },
                "external_ssd": {
                    "detected": False,
                    "capacity_gb": 0,
                    "status": "Unknown"
                },
                "environment_info": {
                    "container": False,
                    "virtualized": False,
                    "hardware_access": "Full"
                }
            }
            
            # Check memory upgrade
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            
            if memory_gb >= 15:  # 16GB configuration
                upgrade_status["ram_upgrade"] = {
                    "detected": True,
                    "capacity_gb": round(memory_gb, 2),
                    "status": "Verified - Upgrade Successful",
                    "utilization": f"{memory.percent:.1f}%",
                    "available_gb": round(memory.available / (1024**3), 2)
                }
            
            # Check environment limitations
            try:
                virt_result = subprocess.run(['systemd-detect-virt'], 
                                           capture_output=True, text=True, timeout=3)
                if virt_result.returncode == 0:
                    virt_type = virt_result.stdout.strip()
                    upgrade_status["environment_info"] = {
                        "container": virt_type == "docker",
                        "virtualized": virt_type != "none",
                        "hardware_access": "Limited" if virt_type in ["docker", "container"] else "Full",
                        "environment": virt_type
                    }
            except:
                pass
            
            return upgrade_status
            
        except Exception as e:
            logger.error(f"Failed to check upgrade status: {e}")
            return {"error": str(e)}
    
    async def _scan_external_devices(self) -> Dict[str, Any]:
        """Scan for external storage devices"""
        try:
            external_info = {
                "total_external_devices": 0,
                "ssd_devices": [],
                "usb_devices": [],
                "detection_method": "limited",
                "recommendations": []
            }
            
            # Check for additional block devices beyond the primary
            try:
                with open('/proc/partitions', 'r') as f:
                    partitions = f.read()
                    
                # Look for devices beyond vda (virtual disk a)
                device_count = 0
                for line in partitions.split('\n'):
                    if line.strip() and not line.startswith('major'):
                        parts = line.split()
                        if len(parts) >= 4:
                            device_name = parts[3]
                            if device_name.startswith(('sd', 'nvme', 'vdb', 'vdc')):
                                device_count += 1
                                size_blocks = int(parts[2])
                                size_gb = (size_blocks * 1024) / (1024**3)
                                
                                external_info["ssd_devices"].append({
                                    "device": f"/dev/{device_name}",
                                    "size_gb": round(size_gb, 1),
                                    "type": "block_device"
                                })
                
                external_info["total_external_devices"] = device_count
                
            except Exception as e:
                logger.warning(f"Could not scan block devices: {e}")
            
            # Add recommendations based on environment
            if external_info["total_external_devices"] == 0:
                external_info["recommendations"] = [
                    "Check physical system outside container for external SSD",
                    "Verify USB/SATA connections on host system",
                    "Run 'lsblk -f' on host system to detect external drives",
                    "Check mount points: /media/*, /mnt/*"
                ]
            
            return external_info
            
        except Exception as e:
            logger.error(f"Failed to scan external devices: {e}")
            return {"error": str(e)}


# Global hardware monitor instance
frank_hardware = FrankHardwareMonitor()