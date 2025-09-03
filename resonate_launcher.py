#!/usr/bin/env python3
"""
REZONATE System Launcher
Launch script for the REZONATE modular wearable instrument system.
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('resonate')


class ResonateComponent:
    """Base class for REZONATE system components."""
    
    def __init__(self, name: str, description: str, command: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.command = command or []
        self.process = None
        self.started = False
    
    async def start(self) -> bool:
        """Start the component."""
        if self.started:
            logger.warning(f"{self.name} is already running")
            return True
        
        if not self.command:
            logger.info(f"Starting {self.name} (mock mode)")
            self.started = True
            return True
        
        try:
            logger.info(f"Starting {self.name}: {' '.join(self.command)}")
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.started = True
            logger.info(f"{self.name} started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start {self.name}: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the component."""
        if not self.started:
            return True
        
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=10)
            except asyncio.TimeoutError:
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
    """Main launcher for the REZONATE system."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "resonate_config.json"
        self.components = {}
        self.config = {}
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize REZONATE components."""
        
        # Performance UI Component
        self.components['performance-ui'] = ResonateComponent(
            name="Performance UI",
            description="Real-time performance interface for REZONATE",
            command=self._get_ui_command()
        )
        
        # Bluetooth Orchestration Component
        self.components['bluetooth-orchestration'] = ResonateComponent(
            name="Bluetooth Orchestration",
            description="Device discovery and network management",
            command=self._get_bluetooth_command()
        )
        
        # MIDI Mapping Component
        self.components['midi-mapping'] = ResonateComponent(
            name="MIDI Mapping",
            description="MIDI parameter mapping and DAW integration",
            command=self._get_midi_command()
        )
        
        # Hardware Monitor Component
        self.components['hardware-monitor'] = ResonateComponent(
            name="Hardware Monitor",
            description="Sensor data collection and device health monitoring"
        )
        
        # System Coordinator
        self.components['system-coordinator'] = ResonateComponent(
            name="System Coordinator",
            description="Central coordination and synchronization service"
        )
    
    def _get_ui_command(self) -> List[str]:
        """Get command for Performance UI component."""
        ui_path = Path("software/performance-ui")
        if ui_path.exists():
            if (ui_path / "package.json").exists():
                return ["npm", "start"]
            elif (ui_path / "main.py").exists():
                return ["python3", "main.py"]
        return []
    
    def _get_bluetooth_command(self) -> List[str]:
        """Get command for Bluetooth Orchestration component."""
        bt_path = Path("software/bluetooth-orchestration")
        if bt_path.exists():
            if (bt_path / "app.py").exists():
                return ["python3", "app.py"]
        return []
    
    def _get_midi_command(self) -> List[str]:
        """Get command for MIDI Mapping component."""
        midi_path = Path("software/midi-mapping")
        if midi_path.exists():
            if (midi_path / "mapping_engine.py").exists():
                return ["python3", "mapping_engine.py"]
        return []
    
    def load_config(self) -> Dict:
        """Load launcher configuration."""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                    logger.info(f"Loaded configuration from {self.config_path}")
            else:
                self.config = self._get_default_config()
                self.save_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = self._get_default_config()
        
        return self.config
    
    def save_config(self) -> bool:
        """Save launcher configuration."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "rezonate": {
                "name": "REZONATE Modular Wearable Instrument System",
                "version": "1.0.0",
                "auto_start_components": [
                    "performance-ui",
                    "bluetooth-orchestration", 
                    "midi-mapping"
                ],
                "startup_delay_seconds": 2
            },
            "components": {
                "performance-ui": {
                    "enabled": True,
                    "port": 3000,
                    "auto_restart": True
                },
                "bluetooth-orchestration": {
                    "enabled": True,
                    "scan_interval": 5,
                    "max_devices": 10
                },
                "midi-mapping": {
                    "enabled": True,
                    "default_mapping": "basic"
                },
                "hardware-monitor": {
                    "enabled": True,
                    "sensor_poll_rate": 100
                },
                "system-coordinator": {
                    "enabled": True,
                    "sync_interval": 1000
                }
            }
        }
    
    async def start_all(self, components: Optional[List[str]] = None) -> bool:
        """Start all or specified REZONATE components."""
        self.load_config()
        
        components_to_start = components or self.config.get("rezonate", {}).get("auto_start_components", [])
        
        if not components_to_start:
            components_to_start = list(self.components.keys())
        
        logger.info("🎵 Starting REZONATE System")
        logger.info("=" * 50)
        
        startup_delay = self.config.get("rezonate", {}).get("startup_delay_seconds", 2)
        success_count = 0
        
        for component_name in components_to_start:
            if component_name not in self.components:
                logger.warning(f"Unknown component: {component_name}")
                continue
            
            component = self.components[component_name]
            component_config = self.config.get("components", {}).get(component_name, {})
            
            if not component_config.get("enabled", True):
                logger.info(f"Skipping disabled component: {component_name}")
                continue
            
            success = await component.start()
            if success:
                success_count += 1
                logger.info(f"✓ {component.description}")
            else:
                logger.error(f"✗ Failed to start {component.description}")
            
            await asyncio.sleep(startup_delay)
        
        logger.info("=" * 50)
        if success_count > 0:
            logger.info(f"🚀 REZONATE System operational ({success_count} components)")
            return True
        else:
            logger.error("❌ Failed to start REZONATE System")
            return False
    
    async def stop_all(self) -> bool:
        """Stop all REZONATE components."""
        logger.info("Stopping REZONATE System...")
        
        success_count = 0
        for component in self.components.values():
            if await component.stop():
                success_count += 1
        
        logger.info(f"REZONATE System stopped ({success_count} components)")
        return success_count == len(self.components)
    
    def status(self) -> Dict:
        """Get status of all components."""
        status = {
            "system": "REZONATE Modular Wearable Instrument System",
            "timestamp": time.time(),
            "components": {}
        }
        
        for name, component in self.components.items():
            status["components"][name] = {
                "name": component.description,
                "running": component.is_running(),
                "started": component.started
            }
        
        return status
    
    def print_status(self):
        """Print formatted status information."""
        status = self.status()
        
        print("🎵 REZONATE System Status")
        print("=" * 40)
        
        running_count = sum(1 for comp in status["components"].values() if comp["running"])
        total_count = len(status["components"])
        
        print(f"System Status: {running_count}/{total_count} components running")
        print()
        
        for name, comp in status["components"].items():
            status_icon = "🟢" if comp["running"] else "🔴"
            print(f"{status_icon} {comp['name']}")
        
        print()


async def main():
    """Main entry point for REZONATE launcher."""
    parser = argparse.ArgumentParser(
        description="REZONATE Modular Wearable Instrument System Launcher"
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
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    launcher = ResonateLauncher(args.config)
    
    try:
        if args.action == "start":
            success = await launcher.start_all(args.components)
            if success:
                print("\nREZONATE System is running. Press Ctrl+C to stop.")
                try:
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