#!/usr/bin/env python3
"""
Complete Z-areo OBD2 System Test Runner
=======================================

This script runs the complete test suite including:
- Admin profile setup and authentication
- OBD2 bidirectional data gathering
- Proto Yi integration testing
- Web dashboard verification
- Real-time monitoring validation

Usage: python run_complete_test.py
"""

import asyncio
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import structlog

# Configure logging
structlog.configure(
    level="INFO",
    wrapper_class=structlog.make_filtering_bound_logger(20),
)

logger = structlog.get_logger(__name__)

class CompleteTestRunner:
    """Complete test runner for the Z-areo OBD2 system."""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.start_time = datetime.utcnow()
        
    async def run_admin_setup_test(self) -> bool:
        """Run the admin setup and authentication test."""
        logger.info("Running admin setup and authentication test...")
        
        try:
            # Import and run the admin setup
            from setup_admin_and_test_obd2 import OBD2TestRunner
            
            test_runner = OBD2TestRunner()
            report = await test_runner.run_comprehensive_test()
            
            self.test_results["admin_setup"] = {
                "success": True,
                "report": report,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Admin setup test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Admin setup test failed: {e}")
            self.test_results["admin_setup"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            return False
    
    async def run_proto_yi_test(self) -> bool:
        """Run the Proto Yi integration test."""
        logger.info("Running Proto Yi integration test...")
        
        try:
            # Import and run Proto Yi integration
            from proto_yi_integration import run_proto_yi_integration
            
            await run_proto_yi_integration()
            
            # Load the Proto Yi test report
            proto_yi_report_file = Path("proto_yi_test_report.json")
            if proto_yi_report_file.exists():
                with open(proto_yi_report_file) as f:
                    proto_yi_report = json.load(f)
            else:
                proto_yi_report = {"message": "Report file not found"}
            
            self.test_results["proto_yi"] = {
                "success": True,
                "report": proto_yi_report,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Proto Yi integration test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Proto Yi integration test failed: {e}")
            self.test_results["proto_yi"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            return False
    
    async def test_dashboard_integration(self) -> bool:
        """Test the web dashboard integration."""
        logger.info("Testing web dashboard integration...")
        
        try:
            # Test dashboard endpoints
            from src.ballsdeepnit.dashboard.app import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            
            # Test basic endpoints
            dashboard_tests = {}
            
            # Test system status
            try:
                response = client.get("/api/system/status")
                dashboard_tests["system_status"] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code
                }
            except Exception as e:
                dashboard_tests["system_status"] = {"success": False, "error": str(e)}
            
            # Test performance metrics
            try:
                response = client.get("/api/performance/metrics")
                dashboard_tests["performance_metrics"] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code
                }
            except Exception as e:
                dashboard_tests["performance_metrics"] = {"success": False, "error": str(e)}
            
            # Test memory metrics
            try:
                response = client.get("/api/performance/memory")
                dashboard_tests["memory_metrics"] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code
                }
            except Exception as e:
                dashboard_tests["memory_metrics"] = {"success": False, "error": str(e)}
            
            # Test docs endpoint
            try:
                response = client.get("/docs")
                dashboard_tests["api_docs"] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code
                }
            except Exception as e:
                dashboard_tests["api_docs"] = {"success": False, "error": str(e)}
            
            all_passed = all(test["success"] for test in dashboard_tests.values())
            
            self.test_results["dashboard_integration"] = {
                "success": all_passed,
                "tests": dashboard_tests,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Dashboard integration test completed: {'SUCCESS' if all_passed else 'PARTIAL'}")
            return all_passed
            
        except Exception as e:
            logger.error(f"Dashboard integration test failed: {e}")
            self.test_results["dashboard_integration"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            return False
    
    async def test_obd2_bidirectional_capabilities(self) -> bool:
        """Test OBD2 bidirectional capabilities specifically."""
        logger.info("Testing OBD2 bidirectional capabilities...")
        
        try:
            from src.ballsdeepnit.obd2.zareo_system import ZareoOBD2System, ZareoSystemConfig
            from src.ballsdeepnit.obd2.core import AdapterType
            from src.ballsdeepnit.obd2.scanner import ScannerMode
            
            # Create system with virtual adapter for testing
            config = ZareoSystemConfig(
                obd2_adapter_type=AdapterType.VIRTUAL,
                obd2_port="virtual",
                enable_can_sniffer=True,
                enable_mobile_bridge=True,
                enable_data_collection=True
            )
            
            system = ZareoOBD2System(config)
            
            bidirectional_tests = {}
            
            # Test system initialization
            try:
                init_success = await system.initialize()
                bidirectional_tests["initialization"] = {
                    "success": init_success,
                    "message": "System initialized successfully" if init_success else "Failed to initialize"
                }
            except Exception as e:
                bidirectional_tests["initialization"] = {"success": False, "error": str(e)}
            
            # Test scanner configuration
            try:
                if system.scanner:
                    system.scanner.mode = ScannerMode.BIDIRECTIONAL
                    bidirectional_tests["scanner_config"] = {
                        "success": True,
                        "mode": system.scanner.mode.value,
                        "capabilities": system.scanner.capabilities.__dict__
                    }
                else:
                    bidirectional_tests["scanner_config"] = {
                        "success": False,
                        "error": "Scanner not available"
                    }
            except Exception as e:
                bidirectional_tests["scanner_config"] = {"success": False, "error": str(e)}
            
            # Test system start
            try:
                start_success = await system.start()
                bidirectional_tests["system_start"] = {
                    "success": start_success,
                    "is_running": system.is_running
                }
            except Exception as e:
                bidirectional_tests["system_start"] = {"success": False, "error": str(e)}
            
            # Test data collection session
            try:
                if system.is_running:
                    session_id = await system.start_data_collection_session(
                        session_name="bidirectional_test",
                        participant_id="test_user"
                    )
                    
                    # Wait briefly for data collection
                    await asyncio.sleep(2)
                    
                    result = await system.stop_data_collection_session()
                    
                    bidirectional_tests["data_collection"] = {
                        "success": result["success"],
                        "session_id": session_id,
                        "result": result
                    }
                else:
                    bidirectional_tests["data_collection"] = {
                        "success": False,
                        "error": "System not running"
                    }
            except Exception as e:
                bidirectional_tests["data_collection"] = {"success": False, "error": str(e)}
            
            # Test vehicle diagnostic
            try:
                if system.is_running:
                    diagnostic = await system.perform_vehicle_diagnostic()
                    bidirectional_tests["vehicle_diagnostic"] = {
                        "success": True,
                        "diagnostic_codes": len(diagnostic.get("diagnostic_codes", [])),
                        "readiness_tests": len(diagnostic.get("readiness_tests", {}))
                    }
                else:
                    bidirectional_tests["vehicle_diagnostic"] = {
                        "success": False,
                        "error": "System not running"
                    }
            except Exception as e:
                bidirectional_tests["vehicle_diagnostic"] = {"success": False, "error": str(e)}
            
            # Cleanup
            try:
                await system.stop()
            except:
                pass
            
            all_passed = all(test["success"] for test in bidirectional_tests.values())
            
            self.test_results["obd2_bidirectional"] = {
                "success": all_passed,
                "tests": bidirectional_tests,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"OBD2 bidirectional test completed: {'SUCCESS' if all_passed else 'PARTIAL'}")
            return all_passed
            
        except Exception as e:
            logger.error(f"OBD2 bidirectional test failed: {e}")
            self.test_results["obd2_bidirectional"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            return False
    
    async def test_real_time_monitoring(self) -> bool:
        """Test real-time monitoring capabilities."""
        logger.info("Testing real-time monitoring capabilities...")
        
        try:
            from src.ballsdeepnit.obd2.zareo_system import ZareoOBD2System, ZareoSystemConfig
            from src.ballsdeepnit.obd2.core import AdapterType
            
            config = ZareoSystemConfig(
                obd2_adapter_type=AdapterType.VIRTUAL,
                enable_can_sniffer=True,
                enable_mobile_bridge=True
            )
            
            system = ZareoOBD2System(config)
            
            monitoring_tests = {}
            
            # Initialize and start system
            await system.initialize()
            await system.start()
            
            # Test parameter monitoring
            try:
                test_parameters = ['RPM', 'SPEED', 'COOLANT_TEMP']
                monitoring_data = {}
                
                for param in test_parameters:
                    try:
                        if system.obd2_manager:
                            value = await system.obd2_manager.query_parameter(param)
                            monitoring_data[param] = {
                                "success": value is not None,
                                "value": str(value) if value else None
                            }
                        else:
                            monitoring_data[param] = {"success": False, "error": "OBD2 manager not available"}
                    except Exception as e:
                        monitoring_data[param] = {"success": False, "error": str(e)}
                
                monitoring_tests["parameter_monitoring"] = {
                    "success": any(data["success"] for data in monitoring_data.values()),
                    "parameters": monitoring_data
                }
            except Exception as e:
                monitoring_tests["parameter_monitoring"] = {"success": False, "error": str(e)}
            
            # Test CAN sniffer
            try:
                if system.can_sniffer:
                    await system.can_sniffer.start()
                    await asyncio.sleep(1)  # Brief monitoring
                    stats = system.can_sniffer.get_statistics()
                    
                    monitoring_tests["can_sniffer"] = {
                        "success": True,
                        "stats": stats
                    }
                else:
                    monitoring_tests["can_sniffer"] = {
                        "success": False,
                        "error": "CAN sniffer not available"
                    }
            except Exception as e:
                monitoring_tests["can_sniffer"] = {"success": False, "error": str(e)}
            
            # Test mobile bridge
            try:
                if system.mobile_bridge:
                    await system.mobile_bridge.start()
                    bridge_status = {
                        "is_running": system.mobile_bridge.is_running,
                        "connected_clients": len(system.mobile_bridge.connected_clients)
                    }
                    
                    monitoring_tests["mobile_bridge"] = {
                        "success": True,
                        "status": bridge_status
                    }
                else:
                    monitoring_tests["mobile_bridge"] = {
                        "success": False,
                        "error": "Mobile bridge not available"
                    }
            except Exception as e:
                monitoring_tests["mobile_bridge"] = {"success": False, "error": str(e)}
            
            # Cleanup
            await system.stop()
            
            all_passed = all(test["success"] for test in monitoring_tests.values())
            
            self.test_results["real_time_monitoring"] = {
                "success": all_passed,
                "tests": monitoring_tests,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Real-time monitoring test completed: {'SUCCESS' if all_passed else 'PARTIAL'}")
            return all_passed
            
        except Exception as e:
            logger.error(f"Real-time monitoring test failed: {e}")
            self.test_results["real_time_monitoring"] = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            return False
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate the final comprehensive test report."""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall success
        all_tests_passed = all(
            test_result.get("success", False) 
            for test_result in self.test_results.values()
        )
        
        # Count test results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("success", False))
        
        final_report = {
            "test_execution": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "overall_success": all_tests_passed
            },
            "system_capabilities": {
                "admin_authentication": self.test_results.get("admin_setup", {}).get("success", False),
                "obd2_bidirectional": self.test_results.get("obd2_bidirectional", {}).get("success", False),
                "proto_yi_integration": self.test_results.get("proto_yi", {}).get("success", False),
                "web_dashboard": self.test_results.get("dashboard_integration", {}).get("success", False),
                "real_time_monitoring": self.test_results.get("real_time_monitoring", {}).get("success", False)
            },
            "detailed_results": self.test_results,
            "recommendations": self._generate_recommendations(),
            "next_steps": self._generate_next_steps()
        }
        
        return final_report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if not self.test_results.get("admin_setup", {}).get("success", False):
            recommendations.append("Review admin setup and authentication configuration")
        
        if not self.test_results.get("obd2_bidirectional", {}).get("success", False):
            recommendations.append("Check OBD2 adapter configuration and permissions")
        
        if not self.test_results.get("proto_yi", {}).get("success", False):
            recommendations.append("Verify Proto Yi integration and vehicle simulation")
        
        if not self.test_results.get("dashboard_integration", {}).get("success", False):
            recommendations.append("Review web dashboard endpoints and dependencies")
        
        if not self.test_results.get("real_time_monitoring", {}).get("success", False):
            recommendations.append("Check real-time monitoring components and connections")
        
        if not recommendations:
            recommendations.append("All tests passed - system ready for production use")
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generate next steps based on test results."""
        next_steps = [
            "Connect real OBD2 adapter for hardware testing",
            "Configure production database settings",
            "Set up monitoring and logging for production environment",
            "Deploy web dashboard to production server",
            "Create user documentation and training materials"
        ]
        
        return next_steps
    
    async def run_complete_test_suite(self):
        """Run the complete test suite."""
        print("\n" + "="*80)
        print("Z-AREO OBD2 COMPLETE TEST SUITE")
        print("="*80)
        print(f"Started at: {self.start_time.isoformat()}")
        print("="*80)
        
        # Run all tests
        test_phases = [
            ("Admin Setup & Authentication", self.run_admin_setup_test),
            ("OBD2 Bidirectional Capabilities", self.test_obd2_bidirectional_capabilities),
            ("Proto Yi Integration", self.run_proto_yi_test),
            ("Web Dashboard Integration", self.test_dashboard_integration),
            ("Real-time Monitoring", self.test_real_time_monitoring)
        ]
        
        for phase_name, test_func in test_phases:
            print(f"\n🔄 Running {phase_name}...")
            try:
                success = await test_func()
                status = "✅ PASS" if success else "⚠️  PARTIAL"
                print(f"   {status}")
            except Exception as e:
                print(f"   ❌ FAIL: {e}")
        
        # Generate and save final report
        final_report = self.generate_final_report()
        
        report_file = Path("complete_test_report.json")
        with open(report_file, "w") as f:
            json.dump(final_report, f, indent=2)
        
        # Print final summary
        print("\n" + "="*80)
        print("FINAL TEST SUMMARY")
        print("="*80)
        
        print(f"Overall Result: {'✅ ALL TESTS PASSED' if final_report['test_execution']['overall_success'] else '⚠️  SOME TESTS FAILED'}")
        print(f"Duration: {final_report['test_execution']['duration_seconds']:.1f} seconds")
        print(f"Tests Passed: {final_report['test_execution']['passed_tests']}/{final_report['test_execution']['total_tests']}")
        
        print("\nSystem Capabilities:")
        for capability, status in final_report["system_capabilities"].items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {capability.replace('_', ' ').title()}")
        
        print("\nRecommendations:")
        for rec in final_report["recommendations"]:
            print(f"  • {rec}")
        
        print(f"\n📊 Detailed report saved to: {report_file}")
        print("="*80)
        
        return final_report

async def main():
    """Main entry point."""
    runner = CompleteTestRunner()
    
    try:
        final_report = await runner.run_complete_test_suite()
        
        if final_report["test_execution"]["overall_success"]:
            print("\n🎉 ALL TESTS PASSED!")
            print("🚀 Z-areo OBD2 system is fully operational and ready for deployment!")
            sys.exit(0)
        else:
            print("\n⚠️  SOME TESTS FAILED")
            print("📋 Please review the detailed report and recommendations")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())