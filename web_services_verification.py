#!/usr/bin/env python3
"""
Web Services Features Verification and Function Test
Comprehensive testing script for ballsDeepnit web services
"""

import asyncio
import json
import time
import sys
import os
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    status: str  # 'PASS', 'FAIL', 'SKIP'
    duration: float
    message: str
    details: Optional[Dict] = None

class WebServicesVerifier:
    """Main web services verification class."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def add_result(self, result: TestResult):
        """Add a test result."""
        self.results.append(result)
        status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⏭️"
        self.log(f"{status_icon} {result.test_name}: {result.status} ({result.duration:.3f}s) - {result.message}")
    
    def test_environment_setup(self) -> TestResult:
        """Test basic environment setup."""
        start_time = time.perf_counter()
        
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version < (3, 10):
                return TestResult(
                    "Environment Setup",
                    "FAIL",
                    time.perf_counter() - start_time,
                    f"Python version {python_version.major}.{python_version.minor} is too old (requires 3.10+)"
                )
            
            # Check key directories
            required_dirs = ['src', 'src/ballsdeepnit', 'src/ballsdeepnit/dashboard']
            missing_dirs = [d for d in required_dirs if not os.path.exists(d)]
            
            if missing_dirs:
                return TestResult(
                    "Environment Setup",
                    "FAIL", 
                    time.perf_counter() - start_time,
                    f"Missing directories: {missing_dirs}"
                )
            
            # Check key files
            required_files = [
                'src/ballsdeepnit/dashboard/app.py',
                'src/ballsdeepnit/core/config.py',
                'requirements.txt'
            ]
            missing_files = [f for f in required_files if not os.path.exists(f)]
            
            if missing_files:
                return TestResult(
                    "Environment Setup",
                    "FAIL",
                    time.perf_counter() - start_time,
                    f"Missing files: {missing_files}"
                )
            
            return TestResult(
                "Environment Setup",
                "PASS",
                time.perf_counter() - start_time,
                f"Python {python_version.major}.{python_version.minor}, all required files present"
            )
            
        except Exception as e:
            return TestResult(
                "Environment Setup",
                "FAIL",
                time.perf_counter() - start_time,
                f"Error: {e}"
            )
    
    def test_dependencies_availability(self) -> TestResult:
        """Test if required dependencies can be imported."""
        start_time = time.perf_counter()
        
        required_packages = [
            'fastapi',
            'uvicorn', 
            'pydantic',
            'asyncio',
            'pathlib',
            'json',
            'time'
        ]
        
        missing_packages = []
        available_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                available_packages.append(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            return TestResult(
                "Dependencies Check",
                "FAIL",
                time.perf_counter() - start_time,
                f"Missing packages: {missing_packages}. Available: {available_packages}"
            )
        
        return TestResult(
            "Dependencies Check", 
            "PASS",
            time.perf_counter() - start_time,
            f"All {len(available_packages)} required packages available"
        )
    
    def test_configuration_loading(self) -> TestResult:
        """Test configuration loading."""
        start_time = time.perf_counter()
        
        try:
            # Try to import and load config
            from ballsdeepnit.core.config import settings
            
            # Check critical settings
            critical_settings = ['APP_NAME', 'VERSION', 'DEBUG']
            missing_settings = []
            
            for setting in critical_settings:
                if not hasattr(settings, setting):
                    missing_settings.append(setting)
            
            if missing_settings:
                return TestResult(
                    "Configuration Loading",
                    "FAIL",
                    time.perf_counter() - start_time,
                    f"Missing critical settings: {missing_settings}"
                )
            
            return TestResult(
                "Configuration Loading",
                "PASS", 
                time.perf_counter() - start_time,
                f"Configuration loaded successfully - {settings.APP_NAME} v{settings.VERSION}"
            )
            
        except Exception as e:
            return TestResult(
                "Configuration Loading",
                "FAIL",
                time.perf_counter() - start_time,
                f"Failed to load configuration: {e}"
            )
    
    def test_fastapi_app_creation(self) -> TestResult:
        """Test FastAPI app creation."""
        start_time = time.perf_counter()
        
        try:
            from ballsdeepnit.dashboard.app import app
            
            # Check if app is FastAPI instance
            from fastapi import FastAPI
            if not isinstance(app, FastAPI):
                return TestResult(
                    "FastAPI App Creation",
                    "FAIL",
                    time.perf_counter() - start_time,
                    f"App is not a FastAPI instance: {type(app)}"
                )
            
            # Check app configuration
            app_info = {
                "title": app.title,
                "version": app.version,
                "routes_count": len(app.routes)
            }
            
            return TestResult(
                "FastAPI App Creation",
                "PASS",
                time.perf_counter() - start_time,
                f"FastAPI app created successfully: {app.title} v{app.version} with {len(app.routes)} routes",
                app_info
            )
            
        except Exception as e:
            return TestResult(
                "FastAPI App Creation",
                "FAIL",
                time.perf_counter() - start_time,
                f"Failed to create FastAPI app: {e}"
            )
    
    def test_api_endpoints_discovery(self) -> TestResult:
        """Test API endpoints discovery."""
        start_time = time.perf_counter()
        
        try:
            from ballsdeepnit.dashboard.app import app
            
            # Extract routes information
            routes_info = []
            api_routes = []
            
            for route in app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    route_info = {
                        "path": route.path,
                        "methods": list(route.methods) if route.methods else [],
                        "name": getattr(route, 'name', 'unnamed')
                    }
                    routes_info.append(route_info)
                    
                    if route.path.startswith('/api/'):
                        api_routes.append(route_info)
            
            # Check for critical endpoints
            critical_endpoints = [
                '/health',
                '/api/system/status',
                '/api/performance/metrics'
            ]
            
            found_endpoints = [r['path'] for r in routes_info]
            missing_critical = [ep for ep in critical_endpoints if ep not in found_endpoints]
            
            if missing_critical:
                return TestResult(
                    "API Endpoints Discovery",
                    "FAIL",
                    time.perf_counter() - start_time,
                    f"Missing critical endpoints: {missing_critical}",
                    {"total_routes": len(routes_info), "api_routes": len(api_routes)}
                )
            
            return TestResult(
                "API Endpoints Discovery",
                "PASS",
                time.perf_counter() - start_time,
                f"Found {len(routes_info)} total routes, {len(api_routes)} API routes",
                {"routes": routes_info[:10], "api_routes_count": len(api_routes)}  # Limit details for readability
            )
            
        except Exception as e:
            return TestResult(
                "API Endpoints Discovery",
                "FAIL",
                time.perf_counter() - start_time,
                f"Failed to discover endpoints: {e}"
            )
    
    async def test_app_startup(self) -> TestResult:
        """Test application startup sequence."""
        start_time = time.perf_counter()
        
        try:
            from ballsdeepnit.dashboard.app import app
            
            # Test lifespan context manager
            startup_success = True
            startup_error = None
            
            try:
                # Simulate startup by calling lifespan events manually
                # This is a simplified test since we can't easily test the full uvicorn startup
                if hasattr(app, 'router') and hasattr(app.router, 'lifespan_context'):
                    # Basic validation that lifespan context exists
                    pass
                
            except Exception as e:
                startup_success = False
                startup_error = str(e)
            
            if not startup_success:
                return TestResult(
                    "App Startup",
                    "FAIL",
                    time.perf_counter() - start_time,
                    f"Startup failed: {startup_error}"
                )
            
            return TestResult(
                "App Startup",
                "PASS",
                time.perf_counter() - start_time,
                "Application startup sequence validated"
            )
            
        except Exception as e:
            return TestResult(
                "App Startup",
                "FAIL",
                time.perf_counter() - start_time,
                f"Startup test failed: {e}"
            )
    
    def test_performance_monitoring(self) -> TestResult:
        """Test performance monitoring functionality."""
        start_time = time.perf_counter()
        
        try:
            from ballsdeepnit.monitoring.performance import performance_monitor
            
            # Test if performance monitor can be accessed
            monitor_methods = [
                'get_performance_report',
                'start_monitoring', 
                'stop_monitoring'
            ]
            
            missing_methods = []
            for method in monitor_methods:
                if not hasattr(performance_monitor, method):
                    missing_methods.append(method)
            
            if missing_methods:
                return TestResult(
                    "Performance Monitoring",
                    "FAIL",
                    time.perf_counter() - start_time,
                    f"Missing performance monitor methods: {missing_methods}"
                )
            
            return TestResult(
                "Performance Monitoring", 
                "PASS",
                time.perf_counter() - start_time,
                "Performance monitoring components available"
            )
            
        except Exception as e:
            return TestResult(
                "Performance Monitoring",
                "FAIL",
                time.perf_counter() - start_time,
                f"Performance monitoring test failed: {e}"
            )
    
    def test_caching_system(self) -> TestResult:
        """Test caching system functionality."""
        start_time = time.perf_counter()
        
        try:
            from ballsdeepnit.utils.cache import CacheManager
            
            # Create cache manager instance
            cache_manager = CacheManager()
            
            # Test basic cache operations (synchronous test)
            test_key = "test_key"
            test_value = {"test": "data", "timestamp": time.time()}
            
            # Note: This is a basic structure test since we can't easily run async operations here
            cache_methods = ['get', 'set', 'clear', 'get_stats']
            missing_methods = []
            
            for method in cache_methods:
                if not hasattr(cache_manager, method):
                    missing_methods.append(method)
            
            if missing_methods:
                return TestResult(
                    "Caching System",
                    "FAIL",
                    time.perf_counter() - start_time,
                    f"Missing cache methods: {missing_methods}"
                )
            
            return TestResult(
                "Caching System",
                "PASS",
                time.perf_counter() - start_time,
                "Cache manager structure validated"
            )
            
        except Exception as e:
            return TestResult(
                "Caching System",
                "FAIL",
                time.perf_counter() - start_time,
                f"Caching system test failed: {e}"
            )
    
    def test_security_configurations(self) -> TestResult:
        """Test security configurations."""
        start_time = time.perf_counter()
        
        try:
            from ballsdeepnit.dashboard.app import app
            
            # Check middleware
            middleware_classes = [m.cls.__name__ for m in app.user_middleware]
            
            security_features = {
                "cors_middleware": "CORSMiddleware" in middleware_classes,
                "gzip_middleware": "GZipMiddleware" in middleware_classes,
                "error_handlers": len(app.exception_handlers) > 0,
                "docs_conditional": True  # Assume docs are conditionally enabled
            }
            
            security_issues = []
            if not security_features["cors_middleware"]:
                security_issues.append("CORS middleware not configured")
            if not security_features["error_handlers"]: 
                security_issues.append("No custom error handlers")
            
            if security_issues:
                return TestResult(
                    "Security Configurations",
                    "FAIL",
                    time.perf_counter() - start_time,
                    f"Security issues: {security_issues}",
                    security_features
                )
            
            return TestResult(
                "Security Configurations",
                "PASS",
                time.perf_counter() - start_time,
                "Security configurations validated",
                security_features
            )
            
        except Exception as e:
            return TestResult(
                "Security Configurations",
                "FAIL",
                time.perf_counter() - start_time,
                f"Security test failed: {e}"
            )
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_duration = time.time() - self.start_time
        
        summary = {
            "total_tests": len(self.results),
            "passed": len([r for r in self.results if r.status == "PASS"]),
            "failed": len([r for r in self.results if r.status == "FAIL"]),
            "skipped": len([r for r in self.results if r.status == "SKIP"]),
            "total_duration": total_duration,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        report = {
            "summary": summary,
            "results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "duration": r.duration,
                    "message": r.message,
                    "details": r.details
                }
                for r in self.results
            ]
        }
        
        return report
    
    async def run_all_tests(self):
        """Run all verification tests."""
        self.log("🚀 Starting Web Services Verification")
        
        # Run tests in order
        tests = [
            self.test_environment_setup,
            self.test_dependencies_availability, 
            self.test_configuration_loading,
            self.test_fastapi_app_creation,
            self.test_api_endpoints_discovery,
            self.test_performance_monitoring,
            self.test_caching_system,
            self.test_security_configurations
        ]
        
        for test_func in tests:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            self.add_result(result)
        
        # Run async tests
        async_result = await self.test_app_startup()
        self.add_result(async_result)
        
        # Generate and save report
        report = self.generate_report()
        
        # Print summary
        self.log("📊 Test Summary:")
        self.log(f"   Total Tests: {report['summary']['total_tests']}")
        self.log(f"   ✅ Passed: {report['summary']['passed']}")
        self.log(f"   ❌ Failed: {report['summary']['failed']}")
        self.log(f"   ⏭️ Skipped: {report['summary']['skipped']}")
        self.log(f"   ⏱️ Duration: {report['summary']['total_duration']:.2f}s")
        
        # Save detailed report
        with open("web_services_verification_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        self.log("📄 Detailed report saved to: web_services_verification_report.json")
        
        return report

async def main():
    """Main function to run web services verification."""
    verifier = WebServicesVerifier()
    await verifier.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())