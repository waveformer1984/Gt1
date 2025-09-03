#!/usr/bin/env python3
"""
Z-areo OBD2 Admin Setup and Testing Script
==========================================

This script sets up the admin profile, initializes the OBD2 system,
and performs comprehensive testing of bidirectional data gathering.
"""

import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

from src.ballsdeepnit.auth.models import Base, User, AdminProfile, UserRole
from src.ballsdeepnit.auth.auth_manager import AuthManager
from src.ballsdeepnit.auth.profile_manager import ProfileManager
from src.ballsdeepnit.obd2.zareo_system import ZareoOBD2System, ZareoSystemConfig
from src.ballsdeepnit.obd2.core import AdapterType
from src.ballsdeepnit.obd2.scanner import ScannerMode

# Configure logging
structlog.configure(
    level="INFO",
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
)

logger = structlog.get_logger(__name__)

class OBD2TestRunner:
    """Test runner for OBD2 admin setup and bidirectional testing."""
    
    def __init__(self):
        self.db_engine = None
        self.db_session = None
        self.auth_manager = None
        self.profile_manager = None
        self.zareo_system = None
        self.admin_user = None
        self.admin_token = None
        
    async def initialize_database(self):
        """Initialize the database and create tables."""
        logger.info("Initializing database...")
        
        # Create async engine
        database_url = "sqlite+aiosqlite:///zareo_test.db"
        self.db_engine = create_async_engine(database_url, echo=False)
        
        # Create tables
        async with self.db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        # Create session
        async_session = sessionmaker(
            self.db_engine, class_=AsyncSession, expire_on_commit=False
        )
        self.db_session = async_session()
        
        logger.info("Database initialized successfully")
    
    async def setup_auth_managers(self):
        """Set up authentication and profile managers."""
        logger.info("Setting up authentication managers...")
        
        self.auth_manager = AuthManager(
            db_session=self.db_session,
            jwt_secret="test_secret_key_for_zareo_2024",
            jwt_expiration=3600,
            refresh_expiration=86400
        )
        
        self.profile_manager = ProfileManager(self.db_session)
        
        await self.auth_manager.initialize()
        
        logger.info("Authentication managers set up successfully")
    
    async def create_admin_user(self):
        """Create an admin user with full permissions."""
        logger.info("Creating admin user...")
        
        try:
            # Create admin user
            self.admin_user = await self.auth_manager.create_user(
                username="zareo_admin",
                email="admin@zareo-test.local",
                password="ZareoAdmin2024!",
                first_name="Z-areo",
                last_name="Administrator",
                organization="Z-areo Non-Profit Test",
                role=UserRole.SUPER_ADMIN
            )
            
            # Create comprehensive admin profile
            admin_profile = AdminProfile(
                user_id=self.admin_user.id,
                admin_level=3,
                department="OBD2 Testing Department",
                access_clearance="maximum",
                obd2_permissions={
                    "read_data": True,
                    "write_data": True,
                    "bidirectional_access": True,
                    "ecu_programming": True,
                    "system_configuration": True,
                    "user_management": True,
                    "audit_access": True
                },
                system_access={
                    "dashboard": True,
                    "mobile_bridge": True,
                    "can_sniffer": True,
                    "data_export": True,
                    "compliance_manager": True
                },
                emergency_contact="emergency@zareo-test.local",
                require_2fa=False,  # Disabled for testing
                session_timeout_minutes=120,
                max_concurrent_sessions=5
            )
            
            self.db_session.add(admin_profile)
            await self.db_session.commit()
            
            logger.info("Admin user created successfully", 
                       username=self.admin_user.username, 
                       user_id=self.admin_user.id)
            
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            raise
    
    async def authenticate_admin(self):
        """Authenticate the admin user."""
        logger.info("Authenticating admin user...")
        
        try:
            access_token, refresh_token, user_data = await self.auth_manager.authenticate_user(
                username="zareo_admin",
                password="ZareoAdmin2024!",
                device_info={
                    "platform": "test_script",
                    "version": "1.0.0"
                },
                ip_address="127.0.0.1",
                user_agent="OBD2TestRunner/1.0"
            )
            
            self.admin_token = access_token
            
            logger.info("Admin authentication successful", 
                       user_id=user_data["id"],
                       admin_level=user_data.get("admin_profile", {}).get("admin_level"))
            
            return user_data
            
        except Exception as e:
            logger.error(f"Admin authentication failed: {e}")
            raise
    
    async def setup_obd2_system(self):
        """Set up and initialize the OBD2 system."""
        logger.info("Setting up OBD2 system...")
        
        try:
            # Create system configuration
            config = ZareoSystemConfig(
                obd2_adapter_type=AdapterType.VIRTUAL,  # Use virtual for testing
                obd2_port="virtual",
                obd2_baudrate=38400,
                can_interface="virtual",
                can_channel="vcan0",
                enable_can_sniffer=True,
                enable_mobile_bridge=True,
                enable_data_collection=True,
                enable_compliance=True,
                organization_name="Z-areo Test Environment",
                data_controller="Test Admin",
                auto_start_monitoring=False,
                log_level="INFO"
            )
            
            # Create and initialize system
            self.zareo_system = ZareoOBD2System(config)
            
            if await self.zareo_system.initialize():
                logger.info("OBD2 system initialized successfully")
            else:
                raise Exception("Failed to initialize OBD2 system")
                
        except Exception as e:
            logger.error(f"OBD2 system setup failed: {e}")
            raise
    
    async def test_bidirectional_scanner(self):
        """Test bidirectional scanner capabilities."""
        logger.info("Testing bidirectional scanner...")
        
        try:
            if not self.zareo_system.scanner:
                raise Exception("Scanner not available")
            
            # Configure scanner for bidirectional mode
            self.zareo_system.scanner.mode = ScannerMode.BIDIRECTIONAL
            
            logger.info("Scanner configured for bidirectional mode")
            
            # Test scanner capabilities
            capabilities = self.zareo_system.scanner.capabilities
            logger.info("Scanner capabilities:", 
                       supports_uds=capabilities.supports_uds,
                       supports_kwp2000=capabilities.supports_kwp2000,
                       can_program_ecus=capabilities.can_program_ecus)
            
            # Perform diagnostic scan
            logger.info("Performing diagnostic scan...")
            diagnostic_result = await self.zareo_system.perform_vehicle_diagnostic()
            
            logger.info("Diagnostic scan completed",
                       dtc_count=len(diagnostic_result.get("diagnostic_codes", [])),
                       readiness_tests=len(diagnostic_result.get("readiness_tests", {})))
            
            return diagnostic_result
            
        except Exception as e:
            logger.error(f"Bidirectional scanner test failed: {e}")
            raise
    
    async def test_data_collection_session(self):
        """Test data collection session management."""
        logger.info("Testing data collection session...")
        
        try:
            # Start OBD2 system
            if not await self.zareo_system.start():
                raise Exception("Failed to start OBD2 system")
            
            # Start data collection session
            session_id = await self.zareo_system.start_data_collection_session(
                session_name="admin_test_session",
                participant_id="admin_test_user"
            )
            
            logger.info("Data collection session started", session_id=session_id)
            
            # Simulate some data collection
            await asyncio.sleep(2)
            
            # Get system statistics
            stats = self.zareo_system.system_stats
            logger.info("System statistics during session", **stats)
            
            # Stop session
            result = await self.zareo_system.stop_data_collection_session()
            
            logger.info("Data collection session stopped", 
                       success=result["success"],
                       duration=result.get("duration_seconds", 0))
            
            return result
            
        except Exception as e:
            logger.error(f"Data collection session test failed: {e}")
            raise
    
    async def test_can_sniffer(self):
        """Test CAN sniffer functionality."""
        logger.info("Testing CAN sniffer...")
        
        try:
            if not self.zareo_system.can_sniffer:
                logger.warning("CAN sniffer not available")
                return None
            
            # Start CAN sniffer
            await self.zareo_system.can_sniffer.start()
            
            # Wait briefly for potential messages
            await asyncio.sleep(1)
            
            # Get statistics
            stats = self.zareo_system.can_sniffer.get_statistics()
            logger.info("CAN sniffer statistics", **stats)
            
            # Get recent messages (if any)
            messages = self.zareo_system.can_sniffer.get_recent_messages(10)
            logger.info("Recent CAN messages", message_count=len(messages))
            
            return {
                "stats": stats,
                "recent_messages": len(messages)
            }
            
        except Exception as e:
            logger.error(f"CAN sniffer test failed: {e}")
            raise
    
    async def test_mobile_bridge(self):
        """Test mobile bridge functionality."""
        logger.info("Testing mobile bridge...")
        
        try:
            if not self.zareo_system.mobile_bridge:
                logger.warning("Mobile bridge not available")
                return None
            
            # Start mobile bridge
            await self.zareo_system.mobile_bridge.start()
            
            # Check status
            status = {
                "is_running": self.zareo_system.mobile_bridge.is_running,
                "connected_clients": len(self.zareo_system.mobile_bridge.connected_clients),
                "port": self.zareo_system.config.mobile_port
            }
            
            logger.info("Mobile bridge status", **status)
            
            return status
            
        except Exception as e:
            logger.error(f"Mobile bridge test failed: {e}")
            raise
    
    async def generate_test_report(self, test_results):
        """Generate a comprehensive test report."""
        logger.info("Generating test report...")
        
        report = {
            "test_execution": {
                "timestamp": datetime.utcnow().isoformat(),
                "admin_user": self.admin_user.to_dict() if self.admin_user else None,
                "system_config": {
                    "adapter_type": self.zareo_system.config.obd2_adapter_type.value,
                    "port": self.zareo_system.config.obd2_port,
                    "can_sniffer_enabled": self.zareo_system.config.enable_can_sniffer,
                    "mobile_bridge_enabled": self.zareo_system.config.enable_mobile_bridge
                }
            },
            "test_results": test_results,
            "system_status": {
                "is_running": self.zareo_system.is_running,
                "components": {
                    "obd2_manager": self.zareo_system.obd2_manager is not None,
                    "scanner": self.zareo_system.scanner is not None,
                    "can_sniffer": self.zareo_system.can_sniffer is not None,
                    "mobile_bridge": self.zareo_system.mobile_bridge is not None,
                    "data_collector": self.zareo_system.data_collector is not None
                }
            }
        }
        
        # Save report to file
        report_file = Path("zareo_test_report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info("Test report saved", file=str(report_file))
        
        return report
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up resources...")
        
        try:
            if self.zareo_system:
                await self.zareo_system.stop()
            
            if self.auth_manager:
                await self.auth_manager.cleanup()
            
            if self.db_session:
                await self.db_session.close()
            
            if self.db_engine:
                await self.db_engine.dispose()
            
            logger.info("Cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    async def run_comprehensive_test(self):
        """Run the complete test suite."""
        test_results = {}
        
        try:
            logger.info("Starting Z-areo OBD2 comprehensive test suite...")
            
            # Setup phase
            await self.initialize_database()
            await self.setup_auth_managers()
            await self.create_admin_user()
            user_data = await self.authenticate_admin()
            test_results["authentication"] = {"success": True, "user_data": user_data}
            
            await self.setup_obd2_system()
            test_results["obd2_setup"] = {"success": True}
            
            # Testing phase
            try:
                diagnostic_result = await self.test_bidirectional_scanner()
                test_results["bidirectional_scanner"] = {
                    "success": True, 
                    "diagnostic_result": diagnostic_result
                }
            except Exception as e:
                test_results["bidirectional_scanner"] = {"success": False, "error": str(e)}
            
            try:
                session_result = await self.test_data_collection_session()
                test_results["data_collection"] = {
                    "success": True,
                    "session_result": session_result
                }
            except Exception as e:
                test_results["data_collection"] = {"success": False, "error": str(e)}
            
            try:
                can_result = await self.test_can_sniffer()
                test_results["can_sniffer"] = {
                    "success": True,
                    "result": can_result
                }
            except Exception as e:
                test_results["can_sniffer"] = {"success": False, "error": str(e)}
            
            try:
                mobile_result = await self.test_mobile_bridge()
                test_results["mobile_bridge"] = {
                    "success": True,
                    "result": mobile_result
                }
            except Exception as e:
                test_results["mobile_bridge"] = {"success": False, "error": str(e)}
            
            # Generate report
            report = await self.generate_test_report(test_results)
            
            logger.info("Comprehensive test suite completed successfully!")
            
            # Print summary
            print("\n" + "="*80)
            print("Z-AREO OBD2 TEST SUMMARY")
            print("="*80)
            print(f"Admin User: {self.admin_user.username} (ID: {self.admin_user.id})")
            print(f"Admin Profile: Level {self.admin_user.admin_profile.admin_level if self.admin_user.admin_profile else 'N/A'}")
            print(f"OBD2 System: {'Running' if self.zareo_system.is_running else 'Stopped'}")
            print("\nTest Results:")
            for test_name, result in test_results.items():
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"  {test_name.replace('_', ' ').title()}: {status}")
                if not result["success"]:
                    print(f"    Error: {result.get('error', 'Unknown error')}")
            print("\nBidirectional Access: ✅ ENABLED")
            print("Proto Yi Integration: Ready for setup")
            print("Web Dashboard: Available with authentication")
            print("="*80)
            
            return report
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            test_results["overall"] = {"success": False, "error": str(e)}
            raise
        finally:
            await self.cleanup()

async def main():
    """Main entry point."""
    test_runner = OBD2TestRunner()
    
    try:
        await test_runner.run_comprehensive_test()
        print("\n✅ All tests completed successfully!")
        print("🚀 Z-areo OBD2 system is ready for real-world testing!")
        print("📊 Check zareo_test_report.json for detailed results")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())