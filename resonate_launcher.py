#!/usr/bin/env python3
"""
REZONATE System Launcher - Optimized Version
Launch script for the REZONATE modular wearable instrument system.
Performance optimizations: Parallel startup, caching, monitoring
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set
import psutil  # For performance monitoring

# Try to use uvloop for better async performance
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

# Configure optimized logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler(
            'logs/resonate.log', maxBytes=10485760, backupCount=5
        )
    ]
)
logger = logging.getLogger('resonate')


@dataclass
class ComponentMetrics:
    """Performance metrics for components."""
    start_time: float = 0.0
    startup_duration: float = 0.0
    memory_usage: float = 0.0
    cpu_percent: float = 0.0
    restart_count: int = 0


class ResonateComponent:
    """Enhanced base class for REZONATE system components with monitoring."""
    
    def __init__(self, name: str, description: str, command: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.command = command or []
        self.process = None
        self.started = False
        self.metrics = ComponentMetrics()
        self._monitor_task = None
    
    async def start(self) -> bool:
        """Start the component with performance tracking."""
        if self.started:
            logger.warning(f"{self.name} is already running")
            return True
        
        self.metrics.start_time = time.time()
        
        if not self.command:
            logger.info(f"Starting {self.name} (mock mode)")
            self.started = True
            self.metrics.startup_duration = time.time() - self.metrics.start_time
            return True
        
        try:
            logger.info(f"Starting {self.name}: {' '.join(self.command)}")
            
            # Use more efficient subprocess options
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,  # Better process isolation
                limit=1024*1024  # 1MB buffer limit
            )
            
            self.started = True
            self.metrics.startup_duration = time.time() - self.metrics.start_time
            
            # Start monitoring
            self._monitor_task = asyncio.create_task(self._monitor_process())
            
            logger.info(f"{self.name} started in {self.metrics.startup_duration:.2f}s")
            return True
        except Exception as e:
            logger.error(f"Failed to start {self.name}: {e}")
            return False
    
    async def _monitor_process(self):
        """Monitor process performance metrics."""
        if not self.process:
            return
        
        try:
            proc = psutil.Process(self.process.pid)
            while self.is_running():
                try:
                    self.metrics.memory_usage = proc.memory_info().rss / 1024 / 1024  # MB
                    self.metrics.cpu_percent = proc.cpu_percent(interval=1)
                    await asyncio.sleep(30)  # Check every 30 seconds
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
        except Exception as e:
            logger.debug(f"Monitoring error for {self.name}: {e}")
    
    async def stop(self) -> bool:
        """Stop the component gracefully."""
        if not self.started:
            return True
        
        if self._monitor_task:
            self._monitor_task.cancel()
        
        if self.process:
            try:
                # Try graceful shutdown first
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                # Force kill if needed
                logger.warning(f"Force killing {self.name}")
                self.process.kill()
                await self.process.wait()
            except Exception as e:
                logger.error(f"Error stopping {self.name}: {e}")
                return False
        
        self.started = False
        logger.info(f"{self.name} stopped")
        return True
    
    def is_running(self) -> bool:
        """Check if component is running."""
        if not self.started:
            return False
        
        if self.process:
            return self.process.returncode is None
        
        return self.started


class ResonateLauncher:
    """Optimized launcher for the REZONATE system with parallel startup."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "resonate_config.json"
        self.components = {}
        self.config = {}
        self._config_cache = {}
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize component definitions."""
        self.components = {
            "performance-ui": ResonateComponent(
                "performance-ui",
                "Web UI for Performance Mode",
                ["node", "web/server.js"] if os.path.exists("web/server.js") else None
            ),
            "bluetooth-orchestration": ResonateComponent(
                "bluetooth-orchestration",
                "Bluetooth Device Orchestration Service",
                ["python3", "src/bluetooth_orchestrator.py"] if os.path.exists("src/bluetooth_orchestrator.py") else None
            ),
            "midi-mapping": ResonateComponent(
                "midi-mapping",
                "MIDI Mapping Engine",
                ["python3", "src/midi_mapper.py"] if os.path.exists("src/midi_mapper.py") else None
            ),
            "hardware-monitor": ResonateComponent(
                "hardware-monitor",
                "Hardware Monitoring Service",
                ["python3", "src/hardware_monitor.py"] if os.path.exists("src/hardware_monitor.py") else None
            ),
            "system-coordinator": ResonateComponent(
                "system-coordinator",
                "System Coordination Service",
                ["python3", "src/system_coordinator.py"] if os.path.exists("src/system_coordinator.py") else None
            ),
            "audio-processor": ResonateComponent(
                "audio-processor",
                "Real-time Audio Processing Engine",
                ["python3", "src/audio_processor.py"] if os.path.exists("src/audio_processor.py") else None
            ),
            "gesture-recognition": ResonateComponent(
                "gesture-recognition",
                "Gesture Recognition Service",
                ["python3", "src/gesture_recognizer.py"] if os.path.exists("src/gesture_recognizer.py") else None
            )
        }
    
    @lru_cache(maxsize=1)
    def load_config(self):
        """Load and cache configuration from JSON file."""
        try:
            config_path = Path(self.config_path)
            if config_path.exists():
                # Check if config has changed
                mtime = config_path.stat().st_mtime
                if self._config_cache.get('mtime') != mtime:
                    with open(config_path, 'r') as f:
                        self.config = json.load(f)
                    self._config_cache['mtime'] = mtime
                    self._config_cache['config'] = self.config
                    logger.info(f"Configuration loaded from {self.config_path}")
                else:
                    self.config = self._config_cache.get('config', {})
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._create_default_config()
        
        return self.config
    
    def _create_default_config(self):
        """Create optimized default configuration."""
        self.config = {
            "rezonate": {
                "auto_start_components": [
                    "performance-ui",
                    "system-coordinator",
                    "midi-mapping"
                ],
                "startup_delay_seconds": 0.5,  # Reduced delay
                "parallel_startup": True,  # Enable parallel startup
                "max_parallel_starts": 4,  # Limit concurrent starts
                "restart_policy": {
                    "enabled": True,
                    "max_restarts": 3,
                    "restart_delay": 5
                }
            },
            "performance": {
                "enable_monitoring": True,
                "log_metrics_interval": 60,
                "memory_limit_mb": 512,
                "cpu_limit_percent": 80
            },
            "components": {
                "performance-ui": {
                    "enabled": True,
                    "port": 3000,
                    "auto_restart": True,
                    "priority": 1  # Startup priority
                },
                "bluetooth-orchestration": {
                    "enabled": True,
                    "scan_interval": 5,
                    "max_devices": 10,
                    "priority": 2
                },
                "midi-mapping": {
                    "enabled": True,
                    "default_mapping": "basic",
                    "buffer_size": 256,
                    "priority": 2
                },
                "hardware-monitor": {
                    "enabled": True,
                    "sensor_poll_rate": 100,
                    "priority": 3
                },
                "system-coordinator": {
                    "enabled": True,
                    "sync_interval": 1000,
                    "priority": 1
                }
            }
        }
    
    async def start_all(self, components: Optional[List[str]] = None) -> bool:
        """Start all or specified REZONATE components with parallel execution."""
        self.load_config()
        
        components_to_start = components or self.config.get("rezonate", {}).get("auto_start_components", [])
        
        if not components_to_start:
            components_to_start = list(self.components.keys())
        
        logger.info("🎵 Starting REZONATE System (Optimized)")
        logger.info("=" * 50)
        
        # Sort by priority
        components_to_start = sorted(
            components_to_start,
            key=lambda x: self.config.get("components", {}).get(x, {}).get("priority", 999)
        )
        
        # Check if parallel startup is enabled
        parallel_enabled = self.config.get("rezonate", {}).get("parallel_startup", True)
        max_parallel = self.config.get("rezonate", {}).get("max_parallel_starts", 4)
        
        success_count = 0
        failed_components = []
        
        if parallel_enabled:
            # Start components in parallel batches
            for i in range(0, len(components_to_start), max_parallel):
                batch = components_to_start[i:i + max_parallel]
                tasks = []
                
                for component_name in batch:
                    if component_name not in self.components:
                        logger.warning(f"Unknown component: {component_name}")
                        continue
                    
                    component = self.components[component_name]
                    component_config = self.config.get("components", {}).get(component_name, {})
                    
                    if not component_config.get("enabled", True):
                        logger.info(f"Skipping disabled component: {component_name}")
                        continue
                    
                    tasks.append(self._start_component_async(component_name))
                
                # Wait for batch to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for idx, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Failed to start component: {result}")
                        failed_components.append(batch[idx])
                    elif result:
                        success_count += 1
        else:
            # Sequential startup (fallback)
            startup_delay = self.config.get("rezonate", {}).get("startup_delay_seconds", 2)
            
            for component_name in components_to_start:
                if component_name not in self.components:
                    logger.warning(f"Unknown component: {component_name}")
                    continue
                
                result = await self._start_component_async(component_name)
                if result:
                    success_count += 1
                else:
                    failed_components.append(component_name)
                
                await asyncio.sleep(startup_delay)
        
        logger.info("=" * 50)
        if success_count > 0:
            logger.info(f"🚀 REZONATE System operational ({success_count} components)")
            if failed_components:
                logger.warning(f"⚠️  Failed components: {', '.join(failed_components)}")
            
            # Start performance monitoring
            asyncio.create_task(self._monitor_system_performance())
            return True
        else:
            logger.error("❌ Failed to start REZONATE System")
            return False
    
    async def _start_component_async(self, component_name: str) -> bool:
        """Start a single component asynchronously."""
        component = self.components[component_name]
        component_config = self.config.get("components", {}).get(component_name, {})
        
        logger.info(f"Starting {component.description}...")
        success = await component.start()
        
        if success:
            logger.info(f"✓ {component.description}")
        else:
            logger.error(f"✗ Failed to start {component.description}")
        
        return success
    
    async def _monitor_system_performance(self):
        """Monitor overall system performance."""
        if not self.config.get("performance", {}).get("enable_monitoring", True):
            return
        
        interval = self.config.get("performance", {}).get("log_metrics_interval", 60)
        
        while True:
            try:
                await asyncio.sleep(interval)
                
                # Collect metrics
                total_memory = 0
                total_cpu = 0
                active_count = 0
                
                for component in self.components.values():
                    if component.is_running():
                        active_count += 1
                        total_memory += component.metrics.memory_usage
                        total_cpu += component.metrics.cpu_percent
                
                # System metrics
                system_memory = psutil.virtual_memory().percent
                system_cpu = psutil.cpu_percent(interval=1)
                
                logger.info(
                    f"📊 Performance: Components: {active_count}, "
                    f"Memory: {total_memory:.1f}MB ({system_memory:.1f}% system), "
                    f"CPU: {total_cpu:.1f}% ({system_cpu:.1f}% system)"
                )
                
                # Check limits
                memory_limit = self.config.get("performance", {}).get("memory_limit_mb", 512)
                cpu_limit = self.config.get("performance", {}).get("cpu_limit_percent", 80)
                
                if total_memory > memory_limit:
                    logger.warning(f"⚠️  Memory usage ({total_memory:.1f}MB) exceeds limit ({memory_limit}MB)")
                
                if total_cpu > cpu_limit:
                    logger.warning(f"⚠️  CPU usage ({total_cpu:.1f}%) exceeds limit ({cpu_limit}%)")
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
    
    async def stop_all(self) -> bool:
        """Stop all REZONATE components in parallel."""
        logger.info("Stopping REZONATE System...")
        
        # Stop all components in parallel
        tasks = [component.stop() for component in self.components.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is True)
        logger.info(f"REZONATE System stopped ({success_count} components)")
        
        return success_count == len(self.components)
    
    def status(self) -> Dict:
        """Get enhanced status of all components."""
        status = {
            "system": "REZONATE Modular Wearable Instrument System",
            "timestamp": time.time(),
            "components": {},
            "performance": {
                "total_memory_mb": 0,
                "total_cpu_percent": 0,
                "system_memory_percent": psutil.virtual_memory().percent,
                "system_cpu_percent": psutil.cpu_percent(interval=0.1)
            }
        }
        
        for name, component in self.components.items():
            is_running = component.is_running()
            status["components"][name] = {
                "name": component.description,
                "running": is_running,
                "started": component.started,
                "metrics": {
                    "startup_duration": component.metrics.startup_duration,
                    "memory_mb": component.metrics.memory_usage,
                    "cpu_percent": component.metrics.cpu_percent,
                    "restart_count": component.metrics.restart_count
                }
            }
            
            if is_running:
                status["performance"]["total_memory_mb"] += component.metrics.memory_usage
                status["performance"]["total_cpu_percent"] += component.metrics.cpu_percent
        
        return status
    
    def print_status(self):
        """Print enhanced formatted status information."""
        status = self.status()
        
        print("🎵 REZONATE System Status")
        print("=" * 50)
        
        running_count = sum(1 for comp in status["components"].values() if comp["running"])
        total_count = len(status["components"])
        
        print(f"System Status: {running_count}/{total_count} components running")
        print(f"Memory: {status['performance']['total_memory_mb']:.1f}MB "
              f"(System: {status['performance']['system_memory_percent']:.1f}%)")
        print(f"CPU: {status['performance']['total_cpu_percent']:.1f}% "
              f"(System: {status['performance']['system_cpu_percent']:.1f}%)")
        print()
        
        for name, comp in status["components"].items():
            status_icon = "🟢" if comp["running"] else "🔴"
            metrics = comp["metrics"]
            
            print(f"{status_icon} {comp['name']}")
            if comp["running"]:
                print(f"   ├─ Memory: {metrics['memory_mb']:.1f}MB")
                print(f"   ├─ CPU: {metrics['cpu_percent']:.1f}%")
                print(f"   └─ Startup: {metrics['startup_duration']:.2f}s")
        
        print()


async def main():
    """Main entry point for REZONATE launcher."""
    parser = argparse.ArgumentParser(
        description="REZONATE Modular Wearable Instrument System Launcher (Optimized)"
    )
    parser.add_argument(
        "action",
        choices=["start", "stop", "status", "restart"],
        help="Action to perform"
    )
    parser.add_argument(
        "--components",
        nargs="+",
        help="Specific components to start (default: all enabled)"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Enable parallel component startup (default: True)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create logs directory if needed
    os.makedirs("logs", exist_ok=True)
    
    launcher = ResonateLauncher(args.config)
    
    try:
        if args.action == "start":
            success = await launcher.start_all(args.components)
            if success:
                print("\nREZONATE System is running. Press Ctrl+C to stop.")
                try:
                    # Keep running until interrupted
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    print("\nShutting down REZONATE System...")
                    await launcher.stop_all()
                    print("REZONATE System stopped.")
            else:
                sys.exit(1)
        
        elif args.action == "stop":
            await launcher.stop_all()
        
        elif args.action == "status":
            launcher.print_status()
        
        elif args.action == "restart":
            await launcher.stop_all()
            await asyncio.sleep(2)
            success = await launcher.start_all(args.components)
            if not success:
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        await launcher.stop_all()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)