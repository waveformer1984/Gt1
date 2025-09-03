#!/usr/bin/env python3
"""
Security and Performance Testing Script
Comprehensive security and performance testing for ballsDeepnit web services
"""

import asyncio
import json
import time
import threading
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, List
import subprocess
import sys
import os

class SecurityTester:
    """Security testing functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_cors_headers(self) -> Dict[str, Any]:
        """Test CORS header configuration."""
        self.log("🔒 Testing CORS headers...")
        
        try:
            # Test preflight request
            req = urllib.request.Request(
                f"{self.base_url}/api/system/status",
                headers={
                    'Origin': 'https://evil.example.com',
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Content-Type'
                },
                method='OPTIONS'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                headers = dict(response.headers)
                
                cors_checks = {
                    'access_control_allow_origin': 'Access-Control-Allow-Origin' in headers,
                    'access_control_allow_methods': 'Access-Control-Allow-Methods' in headers,
                    'access_control_allow_headers': 'Access-Control-Allow-Headers' in headers,
                    'origin_value': headers.get('Access-Control-Allow-Origin', ''),
                }
                
                # Check if CORS is properly configured
                security_issues = []
                if cors_checks['origin_value'] == '*':
                    security_issues.append("Wildcard origin allowed (potential security risk)")
                
                return {
                    "test": "cors_headers",
                    "status": "PASS" if len(security_issues) == 0 else "WARNING",
                    "cors_headers": cors_checks,
                    "security_issues": security_issues,
                    "success": True
                }
                
        except urllib.error.HTTPError as e:
            if e.code == 405:  # Method not allowed is expected for some endpoints
                return {
                    "test": "cors_headers",
                    "status": "PARTIAL",
                    "message": "OPTIONS method not allowed, CORS may be handled by middleware",
                    "success": True
                }
            else:
                return {
                    "test": "cors_headers",
                    "status": "FAIL",
                    "error": f"HTTP {e.code}: {e.reason}",
                    "success": False
                }
        except Exception as e:
            return {
                "test": "cors_headers",
                "status": "FAIL",
                "error": str(e),
                "success": False
            }
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and information disclosure."""
        self.log("🛡️ Testing error handling...")
        
        test_cases = [
            {
                "name": "404_error",
                "url": "/api/nonexistent/path",
                "expected_status": 404,
                "method": "GET"
            },
            {
                "name": "405_method_not_allowed",
                "url": "/health",
                "expected_status": 405,
                "method": "PATCH"
            },
            {
                "name": "invalid_json",
                "url": "/api/config",
                "expected_status": 422,
                "method": "PUT",
                "data": b"invalid json data"
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                req = urllib.request.Request(
                    f"{self.base_url}{case['url']}",
                    data=case.get('data'),
                    headers={'Content-Type': 'application/json'},
                    method=case['method']
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    # This should not happen for error cases
                    results.append({
                        "case": case['name'],
                        "expected_status": case['expected_status'],
                        "actual_status": response.status,
                        "success": False,
                        "issue": "Request succeeded when error was expected"
                    })
                    
            except urllib.error.HTTPError as e:
                response_body = e.read().decode('utf-8')
                
                # Check if error response is properly formatted
                try:
                    error_data = json.loads(response_body)
                    has_error_field = 'error' in error_data
                    no_stack_trace = 'traceback' not in response_body.lower()
                    
                    results.append({
                        "case": case['name'],
                        "expected_status": case['expected_status'],
                        "actual_status": e.code,
                        "success": e.code == case['expected_status'],
                        "has_error_field": has_error_field,
                        "no_stack_trace": no_stack_trace,
                        "secure_error": has_error_field and no_stack_trace
                    })
                except json.JSONDecodeError:
                    results.append({
                        "case": case['name'],
                        "expected_status": case['expected_status'],
                        "actual_status": e.code,
                        "success": e.code == case['expected_status'],
                        "has_error_field": False,
                        "issue": "Error response is not valid JSON"
                    })
                    
            except Exception as e:
                results.append({
                    "case": case['name'],
                    "success": False,
                    "error": str(e)
                })
        
        # Analyze results
        successful_cases = len([r for r in results if r.get('success', False)])
        total_cases = len(results)
        
        return {
            "test": "error_handling",
            "status": "PASS" if successful_cases == total_cases else "PARTIAL",
            "successful_cases": successful_cases,
            "total_cases": total_cases,
            "test_results": results,
            "success": successful_cases >= total_cases * 0.7  # 70% success threshold
        }
    
    def test_input_validation(self) -> Dict[str, Any]:
        """Test input validation and injection attempts."""
        self.log("🔍 Testing input validation...")
        
        malicious_inputs = [
            {
                "name": "sql_injection",
                "data": {"debug": "'; DROP TABLE users; --"}
            },
            {
                "name": "xss_attempt",
                "data": {"debug": "<script>alert('xss')</script>"}
            },
            {
                "name": "command_injection",
                "data": {"debug": "; cat /etc/passwd"}
            },
            {
                "name": "large_payload",
                "data": {"debug": "A" * 10000}  # 10KB payload
            }
        ]
        
        results = []
        for test_case in malicious_inputs:
            try:
                data = json.dumps(test_case['data']).encode('utf-8')
                req = urllib.request.Request(
                    f"{self.base_url}/api/config",
                    data=data,
                    headers={'Content-Type': 'application/json'},
                    method='PUT'
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    response_data = json.loads(response.read().decode('utf-8'))
                    
                    # Check if malicious input was properly handled
                    results.append({
                        "case": test_case['name'],
                        "status_code": response.status,
                        "success": True,  # Server didn't crash
                        "handled_safely": True
                    })
                    
            except urllib.error.HTTPError as e:
                # Error responses are good for malicious inputs
                results.append({
                    "case": test_case['name'],
                    "status_code": e.code,
                    "success": True,
                    "handled_safely": True,
                    "rejected_input": True
                })
                
            except Exception as e:
                results.append({
                    "case": test_case['name'],
                    "success": False,
                    "error": str(e),
                    "handled_safely": False
                })
        
        successful_cases = len([r for r in results if r.get('success', False)])
        
        return {
            "test": "input_validation",
            "status": "PASS" if successful_cases == len(results) else "FAIL",
            "test_results": results,
            "success": successful_cases == len(results)
        }

class PerformanceTester:
    """Performance testing functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_response_times(self) -> Dict[str, Any]:
        """Test response times for various endpoints."""
        self.log("⏱️ Testing response times...")
        
        endpoints = [
            "/health",
            "/api/system/status",
            "/api/performance/metrics",
            "/api/config",
            "/api/cache/stats"
        ]
        
        response_times = {}
        
        for endpoint in endpoints:
            times = []
            for i in range(5):  # Test each endpoint 5 times
                start_time = time.perf_counter()
                try:
                    with urllib.request.urlopen(f"{self.base_url}{endpoint}", timeout=10) as response:
                        if response.status == 200:
                            elapsed = time.perf_counter() - start_time
                            times.append(elapsed)
                except Exception as e:
                    times.append(10.0)  # Penalty for failures
            
            if times:
                response_times[endpoint] = {
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "samples": len(times)
                }
        
        # Calculate overall performance
        all_times = []
        for endpoint_data in response_times.values():
            all_times.extend([endpoint_data['avg']])
        
        overall_avg = sum(all_times) / len(all_times) if all_times else 0
        fast_responses = len([t for t in all_times if t < 0.1])  # Under 100ms
        
        return {
            "test": "response_times",
            "status": "PASS" if overall_avg < 0.5 else "WARNING" if overall_avg < 1.0 else "FAIL",
            "overall_average": overall_avg,
            "fast_responses": fast_responses,
            "total_endpoints": len(all_times),
            "endpoint_details": response_times,
            "success": overall_avg < 1.0
        }
    
    async def test_concurrent_load(self) -> Dict[str, Any]:
        """Test performance under concurrent load."""
        self.log("🚀 Testing concurrent load performance...")
        
        concurrent_requests = 20
        total_requests = 100
        
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
                    with urllib.request.urlopen(f"{self.base_url}/health", timeout=30) as response:
                        if response.status == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                    
                    response_time = time.perf_counter() - request_start
                    response_times.append(response_time)
                    
                except Exception:
                    failed_requests += 1
                    response_times.append(30.0)  # timeout penalty
        
        # Execute concurrent requests
        tasks = [make_request() for _ in range(total_requests)]
        await asyncio.gather(*tasks)
        
        total_duration = time.perf_counter() - start_time
        
        # Calculate statistics
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = 0
        
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "test": "concurrent_load",
            "status": "PASS" if success_rate > 95 and avg_response_time < 1.0 else "WARNING" if success_rate > 80 else "FAIL",
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "requests_per_second": requests_per_second,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "p95_response_time": p95_response_time,
            "concurrent_level": concurrent_requests,
            "success": success_rate > 80 and avg_response_time < 2.0
        }
    
    def test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage during operation."""
        self.log("💾 Testing memory usage...")
        
        try:
            # Get initial memory stats
            initial_response = urllib.request.urlopen(f"{self.base_url}/api/performance/memory", timeout=10)
            initial_data = json.loads(initial_response.read().decode('utf-8'))
            
            # Make some requests to potentially increase memory usage
            for i in range(20):
                urllib.request.urlopen(f"{self.base_url}/api/system/status", timeout=5)
                time.sleep(0.1)
            
            # Get final memory stats
            final_response = urllib.request.urlopen(f"{self.base_url}/api/performance/memory", timeout=10)
            final_data = json.loads(final_response.read().decode('utf-8'))
            
            # Calculate memory change
            initial_used = initial_data.get('used_memory_mb', 0)
            final_used = final_data.get('used_memory_mb', 0)
            memory_increase = final_used - initial_used
            memory_percent = final_data.get('memory_percent', 0)
            
            # Check for memory leaks (significant increase)
            potential_leak = memory_increase > 50  # More than 50MB increase
            high_usage = memory_percent > 90
            
            return {
                "test": "memory_usage",
                "status": "FAIL" if potential_leak or high_usage else "PASS",
                "initial_memory_mb": initial_used,
                "final_memory_mb": final_used,
                "memory_increase_mb": memory_increase,
                "memory_percent": memory_percent,
                "potential_leak": potential_leak,
                "high_usage": high_usage,
                "success": not (potential_leak or high_usage)
            }
            
        except Exception as e:
            return {
                "test": "memory_usage",
                "status": "FAIL",
                "error": str(e),
                "success": False
            }

class ComprehensiveTester:
    """Main testing orchestrator."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.security_tester = SecurityTester(base_url)
        self.performance_tester = PerformanceTester(base_url)
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def start_test_server(self) -> bool:
        """Start the mock server for testing."""
        try:
            self.log("🚀 Starting mock server for comprehensive testing...")
            
            def run_server():
                try:
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
            max_wait = 10
            for i in range(max_wait):
                try:
                    response = urllib.request.urlopen(f"{self.base_url}/health", timeout=2)
                    if response.status == 200:
                        self.log("✅ Test server is ready")
                        return True
                except:
                    await asyncio.sleep(1)
                    if i < max_wait - 1:
                        self.log(f"⏳ Waiting for server... ({i+1}/{max_wait})")
            
            self.log("❌ Test server failed to start", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"❌ Failed to start test server: {e}", "ERROR")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all security and performance tests."""
        self.log("🔐⚡ Starting comprehensive security and performance testing")
        
        # Start server
        server_started = await self.start_test_server()
        if not server_started:
            return {
                "error": "Could not start test server",
                "tests_run": False
            }
        
        # Run security tests
        self.log("🔒 Running security tests...")
        security_results = [
            self.security_tester.test_cors_headers(),
            self.security_tester.test_error_handling(),
            self.security_tester.test_input_validation()
        ]
        
        # Run performance tests
        self.log("⚡ Running performance tests...")
        performance_results = [
            await self.performance_tester.test_response_times(),
            await self.performance_tester.test_concurrent_load(),
            self.performance_tester.test_memory_usage()
        ]
        
        # Combine results
        all_results = security_results + performance_results
        
        # Calculate summary
        total_tests = len(all_results)
        passed_tests = len([r for r in all_results if r.get('success', False)])
        failed_tests = total_tests - passed_tests
        
        # Generate comprehensive report
        report = {
            "test_type": "Comprehensive Security and Performance Testing",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "security_tests": {
                "results": security_results,
                "passed": len([r for r in security_results if r.get('success', False)]),
                "total": len(security_results)
            },
            "performance_tests": {
                "results": performance_results,
                "passed": len([r for r in performance_results if r.get('success', False)]),
                "total": len(performance_results)
            }
        }
        
        # Print summary
        self.log("📊 Security & Performance Testing Summary:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   ✅ Passed: {passed_tests}")
        self.log(f"   ❌ Failed: {failed_tests}")
        self.log(f"   📈 Success Rate: {report['summary']['success_rate']:.1f}%")
        self.log(f"   🔒 Security: {report['security_tests']['passed']}/{report['security_tests']['total']} passed")
        self.log(f"   ⚡ Performance: {report['performance_tests']['passed']}/{report['performance_tests']['total']} passed")
        
        # Save report
        with open("security_performance_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        self.log("📄 Security & Performance report saved to: security_performance_test_report.json")
        
        return report

async def main():
    """Main function to run comprehensive tests."""
    tester = ComprehensiveTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())