#!/usr/bin/env python3
"""
API Endpoint Testing Script
Comprehensive testing of ballsDeepnit web service API endpoints
"""

import asyncio
import json
import time
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import subprocess
import threading
from contextlib import asynccontextmanager

@dataclass
class EndpointTest:
    """Endpoint test configuration."""
    method: str
    path: str
    description: str
    expected_status: int = 200
    payload: Optional[Dict] = None
    headers: Optional[Dict] = None
    timeout: int = 30

@dataclass
class EndpointResult:
    """Endpoint test result."""
    test: EndpointTest
    status_code: Optional[int]
    response_data: Optional[Dict]
    duration: float
    success: bool
    error: Optional[str] = None

class APIEndpointTester:
    """API endpoint testing class."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[EndpointResult] = []
        self.server_process = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def start_test_server(self) -> bool:
        """Start the mock web service for testing."""
        try:
            self.log("🚀 Starting test server...")
            
            # Start mock server in background thread
            def run_server():
                try:
                    # Import and run the mock service
                    from mock_web_service import app
                    import uvicorn
                    uvicorn.run(
                        app,
                        host="127.0.0.1",
                        port=8000,
                        log_level="warning",
                        access_log=False
                    )
                except Exception as e:
                    self.log(f"Server start failed: {e}", "ERROR")
            
            # Start in background thread
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Wait for server to be ready
            max_wait = 15
            for i in range(max_wait):
                try:
                    import urllib.request
                    response = urllib.request.urlopen(f"{self.base_url}/health", timeout=2)
                    if response.status == 200:
                        self.log("✅ Test server is ready")
                        return True
                except:
                    await asyncio.sleep(1)
                    if i < max_wait - 1:
                        self.log(f"⏳ Waiting for server... ({i+1}/{max_wait})")
            
            self.log("❌ Test server failed to start within timeout", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"❌ Failed to start test server: {e}", "ERROR")
            return False
    
    async def test_endpoint(self, test: EndpointTest) -> EndpointResult:
        """Test a single endpoint."""
        start_time = time.perf_counter()
        
        try:
            import urllib.request
            import urllib.parse
            import urllib.error
            
            url = f"{self.base_url}{test.path}"
            
            # Prepare request
            headers = test.headers or {}
            headers.setdefault('Content-Type', 'application/json')
            headers.setdefault('User-Agent', 'ballsDeepnit-API-Tester/1.0')
            
            data = None
            if test.payload:
                data = json.dumps(test.payload).encode('utf-8')
            
            # Create request
            req = urllib.request.Request(url, data=data, headers=headers, method=test.method)
            
            # Make request
            with urllib.request.urlopen(req, timeout=test.timeout) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                status_code = response.status
                
                duration = time.perf_counter() - start_time
                success = status_code == test.expected_status
                
                return EndpointResult(
                    test=test,
                    status_code=status_code,
                    response_data=response_data,
                    duration=duration,
                    success=success
                )
                
        except urllib.error.HTTPError as e:
            duration = time.perf_counter() - start_time
            try:
                response_data = json.loads(e.read().decode('utf-8'))
            except:
                response_data = {"error": "Failed to parse error response"}
            
            success = e.code == test.expected_status
            
            return EndpointResult(
                test=test,
                status_code=e.code,
                response_data=response_data,
                duration=duration,
                success=success,
                error=str(e)
            )
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            return EndpointResult(
                test=test,
                status_code=None,
                response_data=None,
                duration=duration,
                success=False,
                error=str(e)
            )
    
    def get_test_endpoints(self) -> List[EndpointTest]:
        """Get list of endpoints to test."""
        return [
            # Health check
            EndpointTest(
                method="GET",
                path="/health",
                description="Health check endpoint",
                expected_status=200
            ),
            
            # System status
            EndpointTest(
                method="GET", 
                path="/api/system/status",
                description="Get system status",
                expected_status=200
            ),
            
            # Performance metrics
            EndpointTest(
                method="GET",
                path="/api/performance/metrics",
                description="Get performance metrics",
                expected_status=200
            ),
            
            # Memory information
            EndpointTest(
                method="GET",
                path="/api/performance/memory",
                description="Get memory information",
                expected_status=200
            ),
            
            # Performance optimization
            EndpointTest(
                method="POST",
                path="/api/performance/optimize",
                description="Trigger performance optimization",
                expected_status=200
            ),
            
            # Plugin management
            EndpointTest(
                method="GET",
                path="/api/plugins",
                description="Get available plugins",
                expected_status=200
            ),
            
            # Plugin reload
            EndpointTest(
                method="POST",
                path="/api/plugins/voice_recognition/reload",
                description="Reload voice recognition plugin",
                expected_status=200
            ),
            
            # Configuration
            EndpointTest(
                method="GET",
                path="/api/config",
                description="Get application configuration",
                expected_status=200
            ),
            
            # Configuration update
            EndpointTest(
                method="PUT",
                path="/api/config",
                description="Update configuration",
                expected_status=200,
                payload={"debug": False, "max_workers": 16}
            ),
            
            # Cache stats
            EndpointTest(
                method="GET",
                path="/api/cache/stats",
                description="Get cache statistics",
                expected_status=200
            ),
            
            # Cache clear
            EndpointTest(
                method="DELETE",
                path="/api/cache",
                description="Clear cache",
                expected_status=200
            ),
            
            # Test 404 handling
            EndpointTest(
                method="GET",
                path="/api/nonexistent",
                description="Test 404 error handling",
                expected_status=404
            ),
            
            # Test invalid method
            EndpointTest(
                method="PATCH",
                path="/health",
                description="Test method not allowed",
                expected_status=405
            )
        ]
    
    async def run_endpoint_tests(self) -> Dict[str, Any]:
        """Run all endpoint tests."""
        self.log("🔍 Starting API endpoint tests...")
        
        endpoints = self.get_test_endpoints()
        
        for endpoint in endpoints:
            self.log(f"🧪 Testing {endpoint.method} {endpoint.path} - {endpoint.description}")
            
            result = await self.test_endpoint(endpoint)
            self.results.append(result)
            
            # Log result
            status_icon = "✅" if result.success else "❌"
            status_msg = f"Status: {result.status_code}" if result.status_code else "No Response"
            self.log(f"   {status_icon} {status_msg} ({result.duration:.3f}s)")
            
            if not result.success and result.error:
                self.log(f"   ⚠️  Error: {result.error}")
            
            # Add small delay between requests
            await asyncio.sleep(0.1)
        
        return self.generate_endpoint_report()
    
    def generate_endpoint_report(self) -> Dict[str, Any]:
        """Generate endpoint test report."""
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.success])
        failed_tests = total_tests - successful_tests
        
        avg_duration = sum(r.duration for r in self.results) / total_tests if total_tests > 0 else 0
        
        summary = {
            "total_endpoints_tested": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "average_response_time": avg_duration,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        detailed_results = []
        for result in self.results:
            detailed_results.append({
                "endpoint": f"{result.test.method} {result.test.path}",
                "description": result.test.description,
                "expected_status": result.test.expected_status,
                "actual_status": result.status_code,
                "success": result.success,
                "duration": result.duration,
                "response_sample": str(result.response_data)[:200] + "..." if result.response_data and len(str(result.response_data)) > 200 else result.response_data,
                "error": result.error
            })
        
        return {
            "summary": summary,
            "detailed_results": detailed_results
        }

class WebSocketTester:
    """WebSocket endpoint testing."""
    
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_websocket_metrics(self) -> Dict[str, Any]:
        """Test WebSocket metrics endpoint."""
        self.log("🔌 Testing WebSocket metrics endpoint...")
        
        try:
            # Try to import websockets (if available)
            try:
                import websockets
                websockets_available = True
            except ImportError:
                websockets_available = False
                self.log("⚠️  websockets library not available, using basic socket test")
                
                # Fallback: try to connect to the endpoint as HTTP to verify it exists
                try:
                    import urllib.request
                    ws_url = f"http://localhost:8000/ws/metrics"
                    # This will fail but tells us if the endpoint is there
                    urllib.request.urlopen(ws_url, timeout=2)
                except urllib.error.HTTPError as e:
                    if e.code == 426:  # Upgrade Required - WebSocket endpoint exists
                        return {
                            "websocket_test": "PARTIAL",
                            "reason": "WebSocket endpoint exists but websockets library not available for full test",
                            "endpoint_exists": True,
                            "success": True
                        }
                except Exception:
                    pass
                
                return {
                    "websocket_test": "SKIPPED",
                    "reason": "websockets library not available",
                    "success": False
                }
            
            if websockets_available:
                ws_url = f"{self.base_url}/ws/metrics"
                
                try:
                    async with websockets.connect(ws_url, timeout=10) as websocket:
                        # Try to receive a few messages
                        messages_received = 0
                        start_time = time.perf_counter()
                        
                        while messages_received < 3 and (time.perf_counter() - start_time) < 10:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5)
                            data = json.loads(message)
                            messages_received += 1
                            self.log(f"📊 Received metrics message {messages_received}")
                        
                        duration = time.perf_counter() - start_time
                        
                        return {
                            "websocket_test": "PASS",
                            "messages_received": messages_received,
                            "duration": duration,
                            "success": True
                        }
                        
                except Exception as e:
                    return {
                        "websocket_test": "FAIL",
                        "error": str(e),
                        "success": False
                    }
        except Exception as e:
            return {
                "websocket_test": "FAIL",
                "error": f"WebSocket test failed: {e}",
                "success": False
            }

class LoadTester:
    """Load testing functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def run_load_test(self, concurrent_requests: int = 10, total_requests: int = 100) -> Dict[str, Any]:
        """Run a basic load test."""
        self.log(f"⚡ Starting load test: {concurrent_requests} concurrent, {total_requests} total requests")
        
        start_time = time.perf_counter()
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def make_request():
            nonlocal successful_requests, failed_requests
            async with semaphore:
                request_start = time.perf_counter()
                try:
                    import urllib.request
                    with urllib.request.urlopen(f"{self.base_url}/health", timeout=30) as response:
                        if response.status == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                    
                    response_time = time.perf_counter() - request_start
                    response_times.append(response_time)
                    
                except Exception:
                    failed_requests += 1
                    response_times.append(30.0)  # timeout
        
        # Create and run tasks
        tasks = [make_request() for _ in range(total_requests)]
        await asyncio.gather(*tasks)
        
        total_duration = time.perf_counter() - start_time
        
        # Calculate statistics
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "total_duration": total_duration,
            "requests_per_second": requests_per_second,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "concurrent_requests": concurrent_requests
        }

async def run_comprehensive_api_tests():
    """Run comprehensive API tests."""
    print("🚀 Starting Comprehensive API Testing")
    print("=" * 50)
    
    # Initialize testers
    api_tester = APIEndpointTester()
    ws_tester = WebSocketTester()
    load_tester = LoadTester()
    
    # Start test server
    server_started = await api_tester.start_test_server()
    
    if not server_started:
        print("❌ Cannot run API tests without server")
        return {
            "server_startup": "FAILED",
            "api_tests": "SKIPPED",
            "websocket_tests": "SKIPPED",
            "load_tests": "SKIPPED"
        }
    
    # Run API endpoint tests
    api_results = await api_tester.run_endpoint_tests()
    
    # Run WebSocket tests
    ws_results = await ws_tester.test_websocket_metrics()
    
    # Run load tests
    load_results = await load_tester.run_load_test(concurrent_requests=5, total_requests=50)
    
    # Combine results
    full_report = {
        "test_type": "Comprehensive API Testing",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "server_startup": "SUCCESS",
        "api_endpoint_tests": api_results,
        "websocket_tests": ws_results,
        "load_tests": load_results
    }
    
    # Print summary
    print("\n📊 API Testing Summary:")
    print(f"   Endpoints Tested: {api_results['summary']['total_endpoints_tested']}")
    print(f"   ✅ Successful: {api_results['summary']['successful_tests']}")
    print(f"   ❌ Failed: {api_results['summary']['failed_tests']}")
    print(f"   📈 Success Rate: {api_results['summary']['success_rate']:.1f}%")
    print(f"   ⏱️  Avg Response Time: {api_results['summary']['average_response_time']:.3f}s")
    print(f"   🔌 WebSocket Test: {ws_results.get('websocket_test', 'UNKNOWN')}")
    print(f"   ⚡ Load Test: {load_results['successful_requests']}/{load_results['total_requests']} requests ({load_results['success_rate']:.1f}%)")
    print(f"   🚀 Requests/sec: {load_results['requests_per_second']:.1f}")
    
    # Save report
    with open("api_endpoint_test_report.json", "w") as f:
        json.dump(full_report, f, indent=2)
    
    print("\n📄 Detailed report saved to: api_endpoint_test_report.json")
    
    return full_report

if __name__ == "__main__":
    asyncio.run(run_comprehensive_api_tests())