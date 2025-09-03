#!/usr/bin/env python3
"""
Z-areo Non-Profit OBD2 System Startup Script
============================================

Simple script to start the complete Z-areo OBD2 data collection system.
This demonstrates basic usage and provides a ready-to-run example.
"""

import asyncio
import signal
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ballsdeepnit.obd2.zareo_system import create_zareo_system, AdapterType
from ballsdeepnit.obd2.compliance import ProcessingPurpose

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZareoSystemRunner:
    """Simple runner for the Z-areo OBD2 system."""
    
    def __init__(self):
        self.system = None
        self.running = False
        
    async def start(self):
        """Start the Z-areo system with default configuration."""
        try:
            logger.info("🚀 Starting Z-areo Non-Profit OBD2 Data Collection System")
            
            # Create system with sensible defaults
            # For testing, use VIRTUAL adapter. For real use, change to ELM327_SERIAL
            self.system = create_zareo_system(
                adapter_type=AdapterType.VIRTUAL,  # Change to ELM327_SERIAL for real OBD2
                port="/dev/ttyUSB0",  # Adjust port as needed
                enable_can_sniffer=True,
                enable_mobile_bridge=True,
                enable_compliance=True,
                auto_start_monitoring=True,
                default_monitoring_params=['RPM', 'SPEED', 'COOLANT_TEMP', 'ENGINE_LOAD'],
                mobile_port=8765
            )
            
            # Initialize all components
            if not await self.system.initialize():
                logger.error("❌ Failed to initialize Z-areo system")
                return False
            
            # Start the system
            if not await self.system.start():
                logger.error("❌ Failed to start Z-areo system")
                return False
            
            self.running = True
            
            # Print system status
            status = self.system.get_system_status()
            logger.info("✅ Z-areo system started successfully!")
            logger.info(f"📱 Mobile app: Connect to ws://localhost:8765")
            logger.info(f"🌐 REST API: http://localhost:8765/api")
            logger.info(f"🔧 System running: {status['system_running']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting system: {e}")
            return False
    
    async def run_demo_session(self):
        """Run a demonstration data collection session."""
        try:
            logger.info("🔬 Starting demonstration data collection session")
            
            # Start a data collection session
            session_id = await self.system.start_data_collection_session(
                session_name="demo_session",
                participant_id="demo_participant_001",
                purposes=[ProcessingPurpose.RESEARCH, ProcessingPurpose.SAFETY_ANALYSIS]
            )
            
            logger.info(f"📊 Data collection session started: {session_id}")
            
            # Let it collect data for 30 seconds
            logger.info("⏱️  Collecting data for 30 seconds...")
            await asyncio.sleep(30)
            
            # Perform a diagnostic scan
            logger.info("🔍 Performing vehicle diagnostic scan...")
            diagnostic = await self.system.perform_vehicle_diagnostic()
            
            logger.info(f"🚗 Vehicle diagnostics completed:")
            logger.info(f"   - VIN: {diagnostic.get('vehicle_info', {}).get('vin', 'Unknown')}")
            logger.info(f"   - Diagnostic codes: {len(diagnostic.get('diagnostic_codes', []))}")
            logger.info(f"   - Enhanced parameters: {len(diagnostic.get('enhanced_parameters', {}))}")
            
            # Stop the session
            result = await self.system.stop_data_collection_session()
            
            if result.get('success'):
                logger.info("✅ Data collection session completed successfully")
                
                # Export the data
                export_path = await self.system.export_session_data(
                    session_id, 'json', anonymize=True
                )
                logger.info(f"📁 Anonymized data exported to: {export_path}")
                
                # Show session summary
                summary = result.get('summary', {})
                logger.info(f"📈 Session Summary:")
                logger.info(f"   - Duration: {summary.get('duration_seconds', 0):.1f} seconds")
                logger.info(f"   - Data points: {summary.get('data_counts', {}).get('obd2_samples', 0)}")
                logger.info(f"   - CAN messages: {summary.get('data_counts', {}).get('can_messages', 0)}")
                
            else:
                logger.error(f"❌ Session failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Error in demo session: {e}")
    
    async def run_continuous(self):
        """Run the system continuously until interrupted."""
        logger.info("🔄 Running Z-areo system continuously...")
        logger.info("📱 Mobile app can connect to: ws://localhost:8765")
        logger.info("🌐 REST API available at: http://localhost:8765/api")
        logger.info("⏹️  Press Ctrl+C to stop")
        
        try:
            while self.running:
                # Show periodic status updates
                status = self.system.get_system_status()
                mobile_clients = status.get('components', {}).get('mobile_bridge', {}).get('connected_clients', 0)
                
                if mobile_clients > 0:
                    logger.info(f"📱 {mobile_clients} mobile client(s) connected")
                
                await asyncio.sleep(60)  # Status update every minute
                
        except KeyboardInterrupt:
            logger.info("⏹️  Interrupt received, stopping system...")
        except Exception as e:
            logger.error(f"❌ Error in continuous mode: {e}")
    
    async def stop(self):
        """Stop the Z-areo system."""
        try:
            self.running = False
            
            if self.system:
                logger.info("🛑 Stopping Z-areo system...")
                await self.system.stop()
                logger.info("✅ Z-areo system stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping system: {e}")

async def main():
    """Main entry point."""
    runner = ZareoSystemRunner()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler():
        logger.info("🛑 Shutdown signal received")
        asyncio.create_task(runner.stop())
    
    # Register signal handlers
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, lambda s, f: signal_handler())
    
    try:
        # Start the system
        if await runner.start():
            
            # Check command line arguments for mode
            if len(sys.argv) > 1 and sys.argv[1] == "--demo":
                # Run demonstration session
                await runner.run_demo_session()
                await runner.stop()
            else:
                # Run continuously
                await runner.run_continuous()
                await runner.stop()
        else:
            logger.error("❌ Failed to start Z-areo system")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        await runner.stop()
        sys.exit(1)

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        Z-areo Non-Profit OBD2 Data Collection System     ║
║                                                           ║
║        🚗 Advanced Vehicle Diagnostics for Research      ║
║        🔬 Privacy-First Data Collection                  ║
║        📱 Mobile Integration & Real-time Monitoring     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Usage:
  python start_zareo_system.py          # Run continuously
  python start_zareo_system.py --demo   # Run demonstration session

""")
    
    # Run the main function
    asyncio.run(main())