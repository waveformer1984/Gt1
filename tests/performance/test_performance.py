"""
Performance tests for ballsDeepnit framework optimizations.
"""

import asyncio
import gc
import pytest
import time
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor

# Performance test markers
pytestmark = pytest.mark.performance


class TestCachePerformance:
    """Test cache system performance."""
    
    @pytest.mark.asyncio
    async def test_cache_set_get_performance(self):
        """Test cache set/get operations performance."""
        from src.ballsdeepnit.utils.cache import CacheManager
        
        cache = CacheManager()
        await cache.initialize()
        
        try:
            # Test data
            test_data = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}
            
            # Measure set performance
            start_time = time.perf_counter()
            
            tasks = []
            for key, value in test_data.items():
                task = cache.set(key, value, ttl=60)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            set_duration = time.perf_counter() - start_time
            
            # Measure get performance
            start_time = time.perf_counter()
            
            get_tasks = []
            for key in test_data.keys():
                task = cache.get(key)
                get_tasks.append(task)
            
            results = await asyncio.gather(*get_tasks)
            get_duration = time.perf_counter() - start_time
            
            # Performance assertions
            assert set_duration < 5.0, f"Cache set took {set_duration:.2f}s, expected < 5s"
            assert get_duration < 2.0, f"Cache get took {get_duration:.2f}s, expected < 2s"
            
            # Verify all values were retrieved
            assert len(results) == len(test_data)
            assert all(result is not None for result in results)
            
            # Calculate operations per second
            set_ops_per_sec = len(test_data) / set_duration
            get_ops_per_sec = len(test_data) / get_duration
            
            assert set_ops_per_sec > 200, f"Set performance: {set_ops_per_sec:.1f} ops/s, expected > 200"
            assert get_ops_per_sec > 500, f"Get performance: {get_ops_per_sec:.1f} ops/s, expected > 500"
            
        finally:
            await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_hit_ratio(self):
        """Test cache hit ratio performance."""
        from src.ballsdeepnit.utils.cache import CacheManager
        
        cache = CacheManager()
        await cache.initialize()
        
        try:
            # Pre-populate cache
            for i in range(100):
                await cache.set(f"popular_key_{i}", f"value_{i}", ttl=60)
            
            # Access pattern: 80% hits, 20% misses
            hits = 0
            misses = 0
            
            for _ in range(1000):
                if hits + misses < 800:  # First 800 should be hits
                    key = f"popular_key_{(hits + misses) % 100}"
                    result = await cache.get(key)
                    if result is not None:
                        hits += 1
                    else:
                        misses += 1
                else:  # Last 200 should be misses
                    key = f"missing_key_{misses}"
                    result = await cache.get(key)
                    if result is None:
                        misses += 1
                    else:
                        hits += 1
            
            hit_ratio = hits / (hits + misses)
            assert hit_ratio > 0.75, f"Hit ratio {hit_ratio:.2%} is below 75%"
            
        finally:
            await cache.close()


class TestLoggingPerformance:
    """Test logging system performance."""
    
    def test_logger_creation_performance(self):
        """Test logger creation and caching performance."""
        from src.ballsdeepnit.utils.logging import get_logger
        
        # Measure logger creation time
        start_time = time.perf_counter()
        
        loggers = []
        for i in range(100):
            logger = get_logger(f"test_logger_{i}")
            loggers.append(logger)
        
        creation_time = time.perf_counter() - start_time
        
        # Should be fast due to caching
        assert creation_time < 0.1, f"Logger creation took {creation_time:.3f}s, expected < 0.1s"
        
        # Test cache effectiveness - second call should be faster
        start_time = time.perf_counter()
        
        cached_loggers = []
        for i in range(100):
            logger = get_logger(f"test_logger_{i}")
            cached_loggers.append(logger)
        
        cached_time = time.perf_counter() - start_time
        
        assert cached_time < creation_time / 2, "Cached logger access should be faster"
    
    def test_log_message_performance(self):
        """Test log message processing performance."""
        from src.ballsdeepnit.utils.logging import get_logger
        
        logger = get_logger("performance_test")
        
        # Measure logging performance
        start_time = time.perf_counter()
        
        for i in range(1000):
            logger.info(f"Performance test message {i}")
        
        logging_time = time.perf_counter() - start_time
        
        # Should handle 1000 messages quickly
        assert logging_time < 2.0, f"Logging 1000 messages took {logging_time:.3f}s, expected < 2s"
        
        messages_per_sec = 1000 / logging_time
        assert messages_per_sec > 500, f"Logging rate: {messages_per_sec:.0f} msg/s, expected > 500"


class TestConfigurationPerformance:
    """Test configuration system performance."""
    
    def test_settings_access_performance(self):
        """Test settings access and caching performance."""
        from src.ballsdeepnit.core.config import settings
        
        # Measure settings access time
        start_time = time.perf_counter()
        
        for _ in range(10000):
            _ = settings.APP_NAME
            _ = settings.DEBUG
            _ = settings.performance.MAX_WORKERS
            _ = settings.enabled_features
        
        access_time = time.perf_counter() - start_time
        
        # Should be very fast due to caching
        assert access_time < 0.5, f"Settings access took {access_time:.3f}s, expected < 0.5s"
        
        accesses_per_sec = 40000 / access_time  # 4 accesses per iteration
        assert accesses_per_sec > 80000, f"Settings access rate: {accesses_per_sec:.0f}/s, expected > 80000"


class TestPerformanceMonitoring:
    """Test performance monitoring system."""
    
    @pytest.mark.asyncio
    async def test_metrics_collection_performance(self):
        """Test metrics collection overhead."""
        from src.ballsdeepnit.monitoring.performance import performance_monitor
        
        # Start monitoring
        await performance_monitor.start_monitoring()
        
        try:
            # Measure the overhead of monitoring
            start_time = time.perf_counter()
            
            # Simulate work while monitoring
            await asyncio.sleep(2)
            
            monitoring_time = time.perf_counter() - start_time
            
            # Get collected metrics
            report = performance_monitor.get_performance_report()
            
            # Monitoring overhead should be minimal
            assert monitoring_time < 2.5, f"Monitoring added {monitoring_time - 2:.3f}s overhead"
            
            # Should have collected metrics
            assert "system" in report
            assert "timestamp" in report
            
        finally:
            await performance_monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_function_tracking_performance(self):
        """Test function performance tracking overhead."""
        from src.ballsdeepnit.monitoring.performance import performance_track
        
        @performance_track("test_function")
        async def tracked_function(n: int) -> int:
            """Test function with performance tracking."""
            await asyncio.sleep(0.001)  # Simulate work
            return n * 2
        
        # Measure performance with tracking
        start_time = time.perf_counter()
        
        tasks = []
        for i in range(100):
            task = tracked_function(i)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        tracked_time = time.perf_counter() - start_time
        
        # Verify results
        assert len(results) == 100
        assert all(results[i] == i * 2 for i in range(100))
        
        # Tracking overhead should be minimal
        expected_time = 0.1  # 100 * 0.001s
        overhead = tracked_time - expected_time
        assert overhead < 0.5, f"Performance tracking added {overhead:.3f}s overhead"


class TestMemoryOptimization:
    """Test memory optimization performance."""
    
    def test_garbage_collection_performance(self):
        """Test garbage collection optimization."""
        from src.ballsdeepnit.monitoring.performance import force_garbage_collection
        
        # Create some objects to be collected
        test_objects = []
        for i in range(10000):
            test_objects.append([f"test_string_{i}" for _ in range(10)])
        
        # Clear references
        del test_objects
        
        # Measure GC performance
        start_time = time.perf_counter()
        gc_result = force_garbage_collection()
        gc_time = time.perf_counter() - start_time
        
        # GC should be fast
        assert gc_time < 1.0, f"Garbage collection took {gc_time:.3f}s, expected < 1s"
        
        # Should have collected objects
        assert gc_result["collected"] > 0, "Garbage collection should have collected objects"
    
    def test_memory_usage_tracking(self):
        """Test memory usage tracking performance."""
        from src.ballsdeepnit.monitoring.performance import get_memory_usage
        
        # Measure memory tracking overhead
        start_time = time.perf_counter()
        
        for _ in range(100):
            memory_info = get_memory_usage()
        
        tracking_time = time.perf_counter() - start_time
        
        # Memory tracking should be fast
        assert tracking_time < 0.5, f"Memory tracking took {tracking_time:.3f}s, expected < 0.5s"
        
        # Should return valid memory info
        assert "rss_mb" in memory_info
        assert "percent" in memory_info
        assert memory_info["rss_mb"] > 0


class TestAsyncPerformance:
    """Test async operation performance."""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent async operations performance."""
        async def dummy_async_operation(n: int) -> int:
            """Dummy async operation for testing."""
            await asyncio.sleep(0.001)  # Simulate I/O
            return n * n
        
        # Test different concurrency levels
        for concurrency in [10, 50, 100]:
            start_time = time.perf_counter()
            
            tasks = []
            for i in range(concurrency):
                task = dummy_async_operation(i)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            operation_time = time.perf_counter() - start_time
            
            # Should complete in reasonable time
            expected_time = 0.001 * 1.5  # Allow 50% overhead
            assert operation_time < expected_time + 0.5, \
                f"Concurrency {concurrency}: {operation_time:.3f}s, expected < {expected_time + 0.5:.3f}s"
            
            # Verify results
            assert len(results) == concurrency
            assert all(results[i] == i * i for i in range(concurrency))
    
    @pytest.mark.asyncio
    async def test_event_loop_performance(self):
        """Test event loop performance characteristics."""
        # Test task scheduling overhead
        start_time = time.perf_counter()
        
        async def noop():
            pass
        
        tasks = []
        for _ in range(1000):
            task = asyncio.create_task(noop())
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        scheduling_time = time.perf_counter() - start_time
        
        # Task scheduling should be efficient
        assert scheduling_time < 1.0, f"Task scheduling took {scheduling_time:.3f}s, expected < 1s"
        
        tasks_per_sec = 1000 / scheduling_time
        assert tasks_per_sec > 1000, f"Task scheduling rate: {tasks_per_sec:.0f}/s, expected > 1000"


@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests for performance regression detection."""
    
    def test_json_serialization_benchmark(self, benchmark):
        """Benchmark JSON serialization performance."""
        test_data = {
            "string": "test" * 100,
            "number": 12345,
            "boolean": True,
            "array": list(range(100)),
            "nested": {"key": "value"} * 50
        }
        
        try:
            import orjson
            result = benchmark(orjson.dumps, test_data)
            assert result is not None
        except ImportError:
            import json
            result = benchmark(json.dumps, test_data)
            assert result is not None
    
    def test_cache_operation_benchmark(self, benchmark):
        """Benchmark cache operations."""
        async def cache_operations():
            from src.ballsdeepnit.utils.cache import CacheManager
            
            cache = CacheManager()
            await cache.initialize()
            
            try:
                # Set and get operations
                await cache.set("benchmark_key", "benchmark_value", ttl=60)
                result = await cache.get("benchmark_key")
                return result
            finally:
                await cache.close()
        
        result = benchmark(asyncio.run, cache_operations())
        assert result == "benchmark_value"
    
    def test_logger_benchmark(self, benchmark):
        """Benchmark logger performance."""
        from src.ballsdeepnit.utils.logging import get_logger
        
        logger = get_logger("benchmark_test")
        
        def log_messages():
            for i in range(100):
                logger.info(f"Benchmark message {i}")
        
        benchmark(log_messages)


# Performance test configuration
def pytest_configure(config):
    """Configure performance tests."""
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark test as a benchmark test"
    )


# Performance test fixtures
@pytest.fixture(scope="session")
def performance_setup():
    """Setup for performance tests."""
    # Ensure optimal GC settings
    gc.set_threshold(1000, 10, 10)
    
    yield
    
    # Cleanup
    gc.collect()


@pytest.fixture
def memory_baseline():
    """Get memory usage baseline for tests."""
    from src.ballsdeepnit.monitoring.performance import get_memory_usage
    
    # Force GC before measurement
    gc.collect()
    baseline = get_memory_usage()
    
    yield baseline
    
    # Check for memory leaks
    gc.collect()
    final_memory = get_memory_usage()
    
    # Allow for some variance in memory usage
    memory_growth = final_memory.get("rss_mb", 0) - baseline.get("rss_mb", 0)
    assert memory_growth < 50, f"Potential memory leak: {memory_growth:.1f}MB growth"