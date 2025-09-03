#!/usr/bin/env python3
"""
WebSocket Testing Script
Dedicated testing for WebSocket functionality in ballsDeepnit web services
"""

import asyncio
import json
import time
import threading
from typing import Dict, Any, List

class WebSocketTester:
    """Comprehensive WebSocket testing."""
    
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def start_mock_server(self) -> bool:
        """Start the mock server for WebSocket testing."""
        try:
            self.log("🚀 Starting mock server for WebSocket tests...")
            
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
                    import urllib.request
                    response = urllib.request.urlopen("http://localhost:8000/health", timeout=2)
                    if response.status == 200:
                        self.log("✅ Mock server is ready")
                        return True
                except:
                    await asyncio.sleep(1)
                    if i < max_wait - 1:
                        self.log(f"⏳ Waiting for server... ({i+1}/{max_wait})")
            
            self.log("❌ Mock server failed to start", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"❌ Failed to start mock server: {e}", "ERROR")
            return False
    
    async def test_websocket_connection(self) -> Dict[str, Any]:
        """Test basic WebSocket connection."""
        self.log("🔌 Testing WebSocket connection...")
        
        try:
            import websockets
            
            ws_url = f"{self.base_url}/ws/metrics"
            start_time = time.perf_counter()
            
            async with websockets.connect(ws_url, timeout=5) as websocket:
                connection_time = time.perf_counter() - start_time
                self.log(f"✅ WebSocket connected successfully ({connection_time:.3f}s)")
                
                return {
                    "test": "websocket_connection",
                    "status": "PASS",
                    "connection_time": connection_time,
                    "success": True
                }
                
        except Exception as e:
            connection_time = time.perf_counter() - start_time
            self.log(f"❌ WebSocket connection failed: {e}")
            return {
                "test": "websocket_connection",
                "status": "FAIL",
                "connection_time": connection_time,
                "error": str(e),
                "success": False
            }
    
    async def test_websocket_metrics_streaming(self) -> Dict[str, Any]:
        """Test WebSocket metrics streaming."""
        self.log("📊 Testing WebSocket metrics streaming...")
        
        try:
            import websockets
            
            ws_url = f"{self.base_url}/ws/metrics"
            messages_received = []
            start_time = time.perf_counter()
            
            async with websockets.connect(ws_url, timeout=10) as websocket:
                # Receive messages for 6 seconds (should get ~3 messages at 2s intervals)
                while (time.perf_counter() - start_time) < 6:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=3)
                        data = json.loads(message)
                        messages_received.append({
                            "timestamp": time.time(),
                            "data": data,
                            "size_bytes": len(message)
                        })
                        self.log(f"📥 Received message {len(messages_received)}: {len(message)} bytes")
                    except asyncio.TimeoutError:
                        break
            
            total_time = time.perf_counter() - start_time
            
            if len(messages_received) >= 2:
                # Calculate message intervals
                intervals = []
                for i in range(1, len(messages_received)):
                    interval = messages_received[i]["timestamp"] - messages_received[i-1]["timestamp"]
                    intervals.append(interval)
                
                avg_interval = sum(intervals) / len(intervals) if intervals else 0
                
                self.log(f"✅ Received {len(messages_received)} messages in {total_time:.1f}s")
                
                return {
                    "test": "websocket_metrics_streaming",
                    "status": "PASS",
                    "messages_received": len(messages_received),
                    "total_time": total_time,
                    "average_interval": avg_interval,
                    "expected_interval": 2.0,
                    "interval_accuracy": abs(avg_interval - 2.0) < 0.5,
                    "sample_data": messages_received[0]["data"] if messages_received else None,
                    "success": True
                }
            else:
                return {
                    "test": "websocket_metrics_streaming",
                    "status": "FAIL",
                    "messages_received": len(messages_received),
                    "total_time": total_time,
                    "error": "Insufficient messages received",
                    "success": False
                }
                
        except Exception as e:
            self.log(f"❌ WebSocket metrics streaming failed: {e}")
            return {
                "test": "websocket_metrics_streaming",
                "status": "FAIL",
                "error": str(e),
                "success": False
            }
    
    async def test_websocket_concurrent_connections(self) -> Dict[str, Any]:
        """Test multiple concurrent WebSocket connections."""
        self.log("🔗 Testing concurrent WebSocket connections...")
        
        try:
            import websockets
            
            concurrent_connections = 3
            ws_url = f"{self.base_url}/ws/metrics"
            successful_connections = 0
            failed_connections = 0
            connection_times = []
            
            async def create_connection():
                nonlocal successful_connections, failed_connections
                try:
                    start_time = time.perf_counter()
                    async with websockets.connect(ws_url, timeout=5) as websocket:
                        connection_time = time.perf_counter() - start_time
                        connection_times.append(connection_time)
                        
                        # Receive one message to verify the connection works
                        message = await asyncio.wait_for(websocket.recv(), timeout=5)
                        json.loads(message)  # Verify it's valid JSON
                        
                        successful_connections += 1
                        self.log(f"✅ Concurrent connection {successful_connections} successful")
                        
                        # Keep connection open for a short time
                        await asyncio.sleep(2)
                        
                except Exception as e:
                    failed_connections += 1
                    self.log(f"❌ Concurrent connection failed: {e}")
            
            # Create concurrent connections
            tasks = [create_connection() for _ in range(concurrent_connections)]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            avg_connection_time = sum(connection_times) / len(connection_times) if connection_times else 0
            
            success = successful_connections >= 2  # At least 2 out of 3 should succeed
            
            result = {
                "test": "websocket_concurrent_connections",
                "status": "PASS" if success else "FAIL",
                "total_attempted": concurrent_connections,
                "successful_connections": successful_connections,
                "failed_connections": failed_connections,
                "average_connection_time": avg_connection_time,
                "success": success
            }
            
            if success:
                self.log(f"✅ Concurrent connections test passed: {successful_connections}/{concurrent_connections}")
            else:
                self.log(f"❌ Concurrent connections test failed: {successful_connections}/{concurrent_connections}")
            
            return result
            
        except Exception as e:
            self.log(f"❌ Concurrent connections test failed: {e}")
            return {
                "test": "websocket_concurrent_connections",
                "status": "FAIL",
                "error": str(e),
                "success": False
            }
    
    async def test_websocket_data_integrity(self) -> Dict[str, Any]:
        """Test WebSocket data integrity and format."""
        self.log("🔍 Testing WebSocket data integrity...")
        
        try:
            import websockets
            
            ws_url = f"{self.base_url}/ws/metrics"
            
            async with websockets.connect(ws_url, timeout=5) as websocket:
                # Receive one message and validate its structure
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                
                # Expected fields in metrics data
                expected_fields = ['cpu_usage', 'memory_usage', 'timestamp']
                missing_fields = [field for field in expected_fields if field not in data]
                
                # Validate data types
                type_validations = []
                if 'cpu_usage' in data:
                    type_validations.append(('cpu_usage', isinstance(data['cpu_usage'], (int, float))))
                if 'memory_usage' in data:
                    type_validations.append(('memory_usage', isinstance(data['memory_usage'], (int, float))))
                if 'timestamp' in data:
                    type_validations.append(('timestamp', isinstance(data['timestamp'], (int, float))))
                
                type_errors = [field for field, valid in type_validations if not valid]
                
                # Check timestamp recency (should be within last 5 seconds)
                current_time = time.time()
                timestamp_recent = abs(current_time - data.get('timestamp', 0)) < 5
                
                success = (
                    len(missing_fields) == 0 and 
                    len(type_errors) == 0 and 
                    timestamp_recent
                )
                
                result = {
                    "test": "websocket_data_integrity",
                    "status": "PASS" if success else "FAIL",
                    "data_sample": data,
                    "missing_fields": missing_fields,
                    "type_errors": type_errors,
                    "timestamp_recent": timestamp_recent,
                    "message_size_bytes": len(message),
                    "success": success
                }
                
                if success:
                    self.log("✅ WebSocket data integrity test passed")
                else:
                    self.log(f"❌ WebSocket data integrity issues: missing={missing_fields}, types={type_errors}")
                
                return result
                
        except Exception as e:
            self.log(f"❌ WebSocket data integrity test failed: {e}")
            return {
                "test": "websocket_data_integrity",
                "status": "FAIL",
                "error": str(e),
                "success": False
            }
    
    async def run_all_websocket_tests(self) -> Dict[str, Any]:
        """Run all WebSocket tests."""
        self.log("🔌 Starting comprehensive WebSocket testing")
        
        # Start mock server
        server_started = await self.start_mock_server()
        if not server_started:
            return {
                "websocket_tests": "FAILED",
                "error": "Could not start mock server",
                "tests": []
            }
        
        # Run all tests
        tests = [
            self.test_websocket_connection(),
            self.test_websocket_metrics_streaming(),
            self.test_websocket_concurrent_connections(),
            self.test_websocket_data_integrity()
        ]
        
        results = []
        for test in tests:
            try:
                result = await test
                results.append(result)
                self.results.append(result)
            except Exception as e:
                self.log(f"❌ Test failed with exception: {e}")
                results.append({
                    "test": "unknown",
                    "status": "FAIL",
                    "error": str(e),
                    "success": False
                })
        
        # Generate summary
        total_tests = len(results)
        passed_tests = len([r for r in results if r.get('success', False)])
        failed_tests = total_tests - passed_tests
        
        summary = {
            "websocket_testing_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "test_results": results
        }
        
        self.log("📊 WebSocket Testing Summary:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   ✅ Passed: {passed_tests}")
        self.log(f"   ❌ Failed: {failed_tests}")
        self.log(f"   📈 Success Rate: {summary['websocket_testing_summary']['success_rate']:.1f}%")
        
        # Save report
        with open("websocket_test_report.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        self.log("📄 WebSocket test report saved to: websocket_test_report.json")
        
        return summary

async def main():
    """Main function to run WebSocket tests."""
    tester = WebSocketTester()
    await tester.run_all_websocket_tests()

if __name__ == "__main__":
    asyncio.run(main())