"""
Z-areo Non-Profit OBD2 Data Collection System
============================================

Main integration system that brings together all OBD2 components:
- Core OBD2 management
- Bidirectional scanner functionality
- Virtual CAN sniffer
- Mobile device integration
- Data collection and storage
- Privacy and compliance management
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
from pathlib import Path

import structlog

from .core import OBD2Manager, OBD2Config, AdapterType
from .scanner import BidirectionalScanner, ScannerMode
from .can_sniffer import VirtualCANSniffer, OBD2_FILTERS
from .mobile_bridge import MobileBridge
from .data_collector import DataCollector
from .compliance import ComplianceManager, ProcessingPurpose

logger = structlog.get_logger(__name__)

@dataclass
class ZareoSystemConfig:
    """Configuration for the Z-areo OBD2 system."""
    # OBD2 Configuration
    obd2_adapter_type: AdapterType = AdapterType.ELM327_SERIAL
    obd2_port: str = "/dev/ttyUSB0"
    obd2_baudrate: int = 38400
    
    # CAN Sniffer Configuration
    can_interface: str = "virtual"
    can_channel: str = "vcan0"
    enable_can_sniffer: bool = True
    
    # Mobile Bridge Configuration
    mobile_port: int = 8765
    enable_mobile_bridge: bool = True
    
    # Data Collection Configuration
    database_url: str = "sqlite:///zareo_vehicle_data.db"
    enable_data_collection: bool = True
    
    # Compliance Configuration
    organization_name: str = "Z-areo Non-Profit"
    data_controller: str = "Z-areo Data Protection Officer"
    enable_compliance: bool = True
    
    # System Configuration
    auto_start_monitoring: bool = False
    default_monitoring_params: List[str] = None
    log_level: str = "INFO"

class ZareoOBD2System:
    """
    Complete Z-areo Non-Profit OBD2 Data Collection System.
    
    This is the main integration class that orchestrates all components
    to provide a comprehensive vehicle data collection solution.
    
    Features:
    - Unified OBD2 data collection
    - Virtual CAN bus monitoring
    - Mobile device integration
    - Data privacy and compliance
    - Research-grade data storage
    - Real-time monitoring and alerts
    """
    
    def __init__(self, config: ZareoSystemConfig):
        self.config = config
        self.is_running = False
        
        # Core components
        self.obd2_manager: Optional[OBD2Manager] = None
        self.scanner: Optional[BidirectionalScanner] = None
        self.can_sniffer: Optional[VirtualCANSniffer] = None
        self.mobile_bridge: Optional[MobileBridge] = None
        self.data_collector: Optional[DataCollector] = None
        self.compliance_manager: Optional[ComplianceManager] = None
        
        # System state
        self.current_session_id: Optional[str] = None
        self.system_stats = {
            'start_time': None,
            'total_sessions': 0,
            'total_data_points': 0,
            'connected_clients': 0
        }
        
    async def initialize(self) -> bool:
        """Initialize all system components."""
        try:
            logger.info("Initializing Z-areo OBD2 System", config=asdict(self.config))
            
            # Initialize compliance manager first
            if self.config.enable_compliance:
                self.compliance_manager = ComplianceManager(
                    organization_name=self.config.organization_name,
                    data_controller=self.config.data_controller
                )
                logger.info("Compliance manager initialized")
            
            # Initialize OBD2 manager
            obd2_config = OBD2Config(
                adapter_type=self.config.obd2_adapter_type,
                port=self.config.obd2_port,
                baudrate=self.config.obd2_baudrate
            )
            
            self.obd2_manager = OBD2Manager(obd2_config)
            
            # Initialize CAN sniffer
            if self.config.enable_can_sniffer:
                self.can_sniffer = VirtualCANSniffer(
                    interface=self.config.can_interface,
                    channel=self.config.can_channel
                )
                
                # Add OBD2 filters by default
                for can_filter in OBD2_FILTERS:
                    self.can_sniffer.filters.append(can_filter)
                
                logger.info("CAN sniffer initialized")
            
            # Initialize bidirectional scanner
            self.scanner = BidirectionalScanner(
                obd2_manager=self.obd2_manager,
                can_sniffer=self.can_sniffer
            )
            
            # Initialize data collector
            if self.config.enable_data_collection:
                self.data_collector = DataCollector(
                    obd2_manager=self.obd2_manager,
                    scanner=self.scanner,
                    can_sniffer=self.can_sniffer,
                    database_url=self.config.database_url
                )
                logger.info("Data collector initialized")
            
            # Initialize mobile bridge
            if self.config.enable_mobile_bridge:
                self.mobile_bridge = MobileBridge(
                    obd2_manager=self.obd2_manager,
                    scanner=self.scanner,
                    can_sniffer=self.can_sniffer,
                    port=self.config.mobile_port
                )
                logger.info("Mobile bridge initialized")
            
            logger.info("Z-areo OBD2 System initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize system", error=str(e))
            return False
    
    async def start(self) -> bool:
        """Start the complete OBD2 data collection system."""
        try:
            if self.is_running:
                logger.warning("System is already running")
                return True
            
            logger.info("Starting Z-areo OBD2 System")
            
            # Connect to OBD2 adapter
            if not await self.obd2_manager.connect():
                logger.error("Failed to connect to OBD2 adapter")
                return False
            
            # Initialize scanner
            if not await self.scanner.initialize():
                logger.error("Failed to initialize scanner")
                return False
            
            # Start CAN sniffer
            if self.can_sniffer and not await self.can_sniffer.start():
                logger.error("Failed to start CAN sniffer")
                return False
            
            # Start mobile bridge
            if self.mobile_bridge and not await self.mobile_bridge.start():
                logger.error("Failed to start mobile bridge")
                return False
            
            # Mark system as running
            self.is_running = True
            self.system_stats['start_time'] = time.time()
            
            # Auto-start monitoring if configured
            if self.config.auto_start_monitoring:
                params = self.config.default_monitoring_params or [
                    'RPM', 'SPEED', 'THROTTLE_POS', 'ENGINE_LOAD', 'COOLANT_TEMP'
                ]
                await self.obd2_manager.start_monitoring(params)
            
            logger.info("Z-areo OBD2 System started successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to start system", error=str(e))
            await self.stop()
            return False
    
    async def stop(self):
        """Stop the complete OBD2 data collection system."""
        try:
            logger.info("Stopping Z-areo OBD2 System")
            
            # Stop current session if active
            if self.current_session_id and self.data_collector:
                await self.data_collector.stop_collection_session()
            
            # Stop mobile bridge
            if self.mobile_bridge:
                await self.mobile_bridge.stop()
            
            # Stop CAN sniffer
            if self.can_sniffer:
                await self.can_sniffer.stop()
            
            # Disconnect from OBD2
            if self.obd2_manager:
                await self.obd2_manager.disconnect()
            
            self.is_running = False
            logger.info("Z-areo OBD2 System stopped")
            
        except Exception as e:
            logger.error("Error stopping system", error=str(e))
    
    async def start_data_collection_session(self, 
                                          session_name: Optional[str] = None,
                                          participant_id: Optional[str] = None,
                                          purposes: List[ProcessingPurpose] = None) -> str:
        """Start a new data collection session with compliance checks."""
        try:
            if not self.is_running:
                raise RuntimeError("System is not running")
            
            if not self.data_collector:
                raise RuntimeError("Data collection is not enabled")
            
            # Register consent if participant ID provided
            if participant_id and self.compliance_manager:
                if not purposes:
                    purposes = [ProcessingPurpose.RESEARCH, ProcessingPurpose.SAFETY_ANALYSIS]
                
                await self.compliance_manager.register_consent(
                    participant_id=participant_id,
                    purposes=purposes,
                    data_types=['vehicle_data', 'diagnostic_codes', 'can_messages']
                )
            
            # Start data collection
            session_id = await self.data_collector.start_collection_session(
                session_name=session_name,
                parameters=self.config.default_monitoring_params
            )
            
            self.current_session_id = session_id
            self.system_stats['total_sessions'] += 1
            
            logger.info("Data collection session started", 
                       session_id=session_id,
                       participant_id=participant_id)
            
            return session_id
            
        except Exception as e:
            logger.error("Failed to start data collection session", error=str(e))
            raise
    
    async def stop_data_collection_session(self) -> Dict[str, Any]:
        """Stop the current data collection session."""
        try:
            if not self.data_collector or not self.current_session_id:
                return {'success': False, 'error': 'No active session'}
            
            result = await self.data_collector.stop_collection_session()
            
            # Generate compliance report
            if self.compliance_manager and result.get('success'):
                privacy_report = self.compliance_manager.generate_privacy_report(
                    self.current_session_id
                )
                result['privacy_report'] = privacy_report
            
            self.current_session_id = None
            return result
            
        except Exception as e:
            logger.error("Failed to stop data collection session", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def perform_vehicle_diagnostic(self) -> Dict[str, Any]:
        """Perform comprehensive vehicle diagnostic scan."""
        try:
            if not self.is_running:
                raise RuntimeError("System is not running")
            
            logger.info("Starting comprehensive vehicle diagnostic")
            
            diagnostic_results = {
                'timestamp': time.time(),
                'vehicle_info': self.obd2_manager.vehicle_info.__dict__,
                'diagnostic_codes': [],
                'enhanced_parameters': {},
                'can_statistics': {},
                'system_status': {}
            }
            
            # Read diagnostic codes
            if self.scanner:
                codes = await self.scanner.read_diagnostic_codes()
                diagnostic_results['diagnostic_codes'] = [asdict(code) for code in codes]
                
                # Read enhanced parameters
                enhanced = await self.scanner.read_enhanced_parameters()
                diagnostic_results['enhanced_parameters'] = enhanced
            
            # Get CAN statistics
            if self.can_sniffer:
                diagnostic_results['can_statistics'] = self.can_sniffer.get_statistics()
            
            # Get system status
            diagnostic_results['system_status'] = self.get_system_status()
            
            logger.info("Vehicle diagnostic completed", 
                       codes_found=len(diagnostic_results['diagnostic_codes']))
            
            return diagnostic_results
            
        except Exception as e:
            logger.error("Failed to perform vehicle diagnostic", error=str(e))
            return {'error': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        status = {
            'system_running': self.is_running,
            'current_session': self.current_session_id,
            'uptime': time.time() - self.system_stats['start_time'] if self.system_stats['start_time'] else 0,
            'statistics': self.system_stats.copy(),
            'components': {}
        }
        
        # OBD2 manager status
        if self.obd2_manager:
            status['components']['obd2'] = self.obd2_manager.get_status()
        
        # Scanner status
        if self.scanner:
            status['components']['scanner'] = self.scanner.get_scanner_status()
        
        # CAN sniffer status
        if self.can_sniffer:
            status['components']['can_sniffer'] = self.can_sniffer.get_statistics()
        
        # Mobile bridge status
        if self.mobile_bridge:
            status['components']['mobile_bridge'] = self.mobile_bridge.get_bridge_status()
        
        # Data collector status
        if self.data_collector:
            status['components']['data_collector'] = self.data_collector.get_collection_status()
        
        # Compliance status
        if self.compliance_manager:
            status['components']['compliance'] = self.compliance_manager.get_compliance_status()
        
        return status
    
    async def export_session_data(self, 
                                session_id: str, 
                                format: str = 'csv',
                                anonymize: bool = True) -> str:
        """Export session data with optional anonymization."""
        try:
            if not self.data_collector:
                raise RuntimeError("Data collection is not enabled")
            
            # Export raw data
            output_path = await self.data_collector.export_session_data(
                session_id=session_id,
                format=format
            )
            
            # Apply anonymization if requested
            if anonymize and self.compliance_manager:
                # Read exported data
                if format.lower() == 'json':
                    with open(output_path, 'r') as f:
                        data = json.load(f)
                    
                    # Anonymize each record
                    anonymized_data = []
                    for record in data:
                        anonymized_record = self.compliance_manager.anonymize_data(record)
                        anonymized_data.append(anonymized_record)
                    
                    # Write anonymized data
                    anonymized_path = output_path.replace('.json', '_anonymized.json')
                    with open(anonymized_path, 'w') as f:
                        json.dump(anonymized_data, f, indent=2)
                    
                    logger.info("Data anonymized and exported", 
                               original=output_path,
                               anonymized=anonymized_path)
                    
                    return anonymized_path
            
            return output_path
            
        except Exception as e:
            logger.error("Failed to export session data", error=str(e))
            raise
    
    def create_mobile_app_config(self) -> Dict[str, Any]:
        """Create configuration for mobile app integration."""
        return {
            'api_endpoint': f"ws://localhost:{self.config.mobile_port}",
            'rest_api': f"http://localhost:{self.config.mobile_port}/api",
            'available_parameters': self.obd2_manager.get_supported_parameters() if self.obd2_manager else [],
            'system_capabilities': {
                'obd2_scanning': True,
                'can_sniffing': self.config.enable_can_sniffer,
                'bidirectional_scanner': True,
                'data_collection': self.config.enable_data_collection,
                'compliance_features': self.config.enable_compliance,
                'real_time_streaming': True,
                'diagnostic_codes': True,
                'actuator_testing': True
            },
            'compliance_info': {
                'organization': self.config.organization_name,
                'data_controller': self.config.data_controller,
                'privacy_features_enabled': self.config.enable_compliance
            }
        }

# Factory function for easy system creation
def create_zareo_system(
    adapter_type: AdapterType = AdapterType.ELM327_SERIAL,
    port: str = "/dev/ttyUSB0",
    enable_can_sniffer: bool = True,
    enable_mobile_bridge: bool = True,
    enable_compliance: bool = True,
    **kwargs
) -> ZareoOBD2System:
    """Factory function to create a Z-areo OBD2 system with common configurations."""
    
    config = ZareoSystemConfig(
        obd2_adapter_type=adapter_type,
        obd2_port=port,
        enable_can_sniffer=enable_can_sniffer,
        enable_mobile_bridge=enable_mobile_bridge,
        enable_compliance=enable_compliance,
        **kwargs
    )
    
    return ZareoOBD2System(config)

# Example usage and testing
async def demo_zareo_system():
    """Demonstration of the Z-areo OBD2 system."""
    
    # Create system with virtual adapter for testing
    system = create_zareo_system(
        adapter_type=AdapterType.VIRTUAL,
        port="virtual",
        enable_can_sniffer=True,
        enable_mobile_bridge=True,
        enable_compliance=True
    )
    
    try:
        # Initialize and start system
        if await system.initialize():
            logger.info("System initialized successfully")
            
            if await system.start():
                logger.info("System started successfully")
                
                # Start a data collection session
                session_id = await system.start_data_collection_session(
                    session_name="demo_session",
                    participant_id="demo_participant"
                )
                
                # Let it run for a few seconds
                await asyncio.sleep(10)
                
                # Perform diagnostic scan
                diagnostic = await system.perform_vehicle_diagnostic()
                logger.info("Diagnostic completed", diagnostic=diagnostic)
                
                # Stop data collection
                result = await system.stop_data_collection_session()
                logger.info("Session stopped", result=result)
                
                # Export data
                if result.get('success'):
                    export_path = await system.export_session_data(session_id, 'json', anonymize=True)
                    logger.info("Data exported", path=export_path)
        
    finally:
        await system.stop()

if __name__ == "__main__":
    # Run demo if executed directly
    asyncio.run(demo_zareo_system())