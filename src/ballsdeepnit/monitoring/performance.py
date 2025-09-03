"""
Advanced performance monitoring and optimization system.
"""

import asyncio
import gc
import psutil
import sys
import time
import threading
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps

try:
    import uvloop
    UVLOOP_AVAILABLE = True
except ImportError:
    UVLOOP_AVAILABLE = False

try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from ..core.config import settings
from ..utils.logging import get_logger, perf_logger


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_rss_mb: float = 0.0
    memory_vms_mb: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    active_threads: int = 0
    open_files: int = 0
    gc_collections: Dict[int, int] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class FunctionMetrics:
    """Metrics for function performance tracking."""
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    last_call: float = 0.0
    memory_impact: float = 0.0


class PerformanceMonitor:
    """High-performance monitoring system with minimal overhead."""
    
    def __init__(self, collection_interval: float = 1.0) -> None:
        self.logger = get_logger(__name__)
        self.collection_interval = collection_interval
        self.metrics_history: deque[PerformanceMetrics] = deque(maxlen=3600)  # 1 hour at 1s intervals
        self.function_metrics: Dict[str, FunctionMetrics] = defaultdict(FunctionMetrics)
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # Performance counters
        self._last_disk_io = None
        self._last_network_io = None
        
        # Setup Prometheus metrics if available
        if PROMETHEUS_AVAILABLE and settings.monitoring.ENABLE_PROMETHEUS:
            self._setup_prometheus_metrics()
    
    def _setup_prometheus_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        self.prometheus_metrics = {
            'cpu_usage': Gauge('ballsdeepnit_cpu_usage_percent', 'CPU usage percentage'),
            'memory_usage': Gauge('ballsdeepnit_memory_usage_percent', 'Memory usage percentage'),
            'memory_rss': Gauge('ballsdeepnit_memory_rss_bytes', 'RSS memory in bytes'),
            'active_threads': Gauge('ballsdeepnit_active_threads', 'Number of active threads'),
            'function_calls': Counter('ballsdeepnit_function_calls_total', 'Total function calls', ['function']),
            'function_duration': Histogram('ballsdeepnit_function_duration_seconds', 'Function execution time', ['function']),
            'gc_collections': Counter('ballsdeepnit_gc_collections_total', 'GC collections', ['generation']),
        }
    
    async def start_monitoring(self) -> None:
        """Start the performance monitoring loop."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.logger.info("Starting performance monitoring")
        
        # Start Prometheus metrics server if enabled
        if PROMETHEUS_AVAILABLE and settings.monitoring.ENABLE_PROMETHEUS:
            try:
                start_http_server(settings.monitoring.PROMETHEUS_PORT)
                self.logger.info(f"Prometheus metrics server started on port {settings.monitoring.PROMETHEUS_PORT}")
            except Exception as e:
                self.logger.warning(f"Failed to start Prometheus server: {e}")
        
        # Start monitoring task
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop the performance monitoring."""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Update Prometheus metrics
                if PROMETHEUS_AVAILABLE and hasattr(self, 'prometheus_metrics'):
                    self._update_prometheus_metrics(metrics)
                
                # Log metrics periodically
                if len(self.metrics_history) % 60 == 0:  # Every minute
                    self._log_performance_summary()
                
                # Check for performance issues
                await self._check_performance_issues(metrics)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.collection_interval)
    
    def _collect_system_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics."""
        try:
            process = psutil.Process()
            
            # CPU and memory
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # I/O statistics
            try:
                io_counters = process.io_counters()
                if self._last_disk_io:
                    disk_read = (io_counters.read_bytes - self._last_disk_io.read_bytes) / 1024 / 1024
                    disk_write = (io_counters.write_bytes - self._last_disk_io.write_bytes) / 1024 / 1024
                else:
                    disk_read = disk_write = 0.0
                self._last_disk_io = io_counters
            except (psutil.AccessDenied, AttributeError):
                disk_read = disk_write = 0.0
            
            # Network statistics
            try:
                net_io = psutil.net_io_counters()
                if self._last_network_io:
                    net_sent = net_io.bytes_sent - self._last_network_io.bytes_sent
                    net_recv = net_io.bytes_recv - self._last_network_io.bytes_recv
                else:
                    net_sent = net_recv = 0
                self._last_network_io = net_io
            except (psutil.AccessDenied, AttributeError):
                net_sent = net_recv = 0
            
            # Thread and file handle counts
            try:
                active_threads = process.num_threads()
                open_files = len(process.open_files())
            except (psutil.AccessDenied, AttributeError):
                active_threads = threading.active_count()
                open_files = 0
            
            # Garbage collection stats
            gc_stats = {i: gc.get_count()[i] for i in range(3)}
            
            return PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_rss_mb=memory_info.rss / 1024 / 1024,
                memory_vms_mb=memory_info.vms / 1024 / 1024,
                disk_io_read_mb=disk_read,
                disk_io_write_mb=disk_write,
                network_bytes_sent=net_sent,
                network_bytes_recv=net_recv,
                active_threads=active_threads,
                open_files=open_files,
                gc_collections=gc_stats,
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return PerformanceMetrics()
    
    def _update_prometheus_metrics(self, metrics: PerformanceMetrics) -> None:
        """Update Prometheus metrics."""
        try:
            self.prometheus_metrics['cpu_usage'].set(metrics.cpu_percent)
            self.prometheus_metrics['memory_usage'].set(metrics.memory_percent)
            self.prometheus_metrics['memory_rss'].set(metrics.memory_rss_mb * 1024 * 1024)
            self.prometheus_metrics['active_threads'].set(metrics.active_threads)
            
            # Update GC metrics
            for gen, count in metrics.gc_collections.items():
                self.prometheus_metrics['gc_collections'].labels(generation=str(gen)).inc(count)
                
        except Exception as e:
            self.logger.error(f"Error updating Prometheus metrics: {e}")
    
    def _log_performance_summary(self) -> None:
        """Log a performance summary."""
        if not self.metrics_history:
            return
        
        latest = self.metrics_history[-1]
        
        # Calculate averages over last minute
        recent_metrics = list(self.metrics_history)[-60:]
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        
        perf_logger.log_metric("system_performance", 1.0, "summary",
            cpu_percent=latest.cpu_percent,
            avg_cpu_1min=avg_cpu,
            memory_percent=latest.memory_percent,
            avg_memory_1min=avg_memory,
            memory_rss_mb=latest.memory_rss_mb,
            active_threads=latest.active_threads,
            open_files=latest.open_files
        )
    
    async def _check_performance_issues(self, metrics: PerformanceMetrics) -> None:
        """Check for performance issues and log warnings."""
        issues = []
        
        # High CPU usage
        if metrics.cpu_percent > 80:
            issues.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        # High memory usage
        if metrics.memory_percent > 85:
            issues.append(f"High memory usage: {metrics.memory_percent:.1f}%")
        
        # Too many threads
        if metrics.active_threads > settings.performance.MAX_WORKERS * 2:
            issues.append(f"High thread count: {metrics.active_threads}")
        
        # Memory growth detection
        if len(self.metrics_history) >= 60:  # At least 1 minute of data
            memory_trend = [m.memory_rss_mb for m in list(self.metrics_history)[-60:]]
            if len(memory_trend) > 10:
                recent_avg = sum(memory_trend[-10:]) / 10
                older_avg = sum(memory_trend[:10]) / 10
                if recent_avg > older_avg * 1.5:  # 50% growth
                    issues.append(f"Potential memory leak detected: {older_avg:.1f}MB -> {recent_avg:.1f}MB")
        
        if issues:
            self.logger.warning(f"Performance issues detected: {'; '.join(issues)}")
    
    @contextmanager
    def measure_function(self, func_name: str):
        """Context manager for measuring function performance."""
        start_time = time.perf_counter()
        start_memory = 0
        
        try:
            process = psutil.Process()
            start_memory = process.memory_info().rss
        except:
            pass
        
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            
            end_memory = 0
            try:
                end_memory = psutil.Process().memory_info().rss
            except:
                pass
            
            memory_impact = (end_memory - start_memory) / 1024 / 1024  # MB
            
            # Update function metrics
            func_metrics = self.function_metrics[func_name]
            func_metrics.call_count += 1
            func_metrics.total_time += duration
            func_metrics.min_time = min(func_metrics.min_time, duration)
            func_metrics.max_time = max(func_metrics.max_time, duration)
            func_metrics.avg_time = func_metrics.total_time / func_metrics.call_count
            func_metrics.last_call = time.time()
            func_metrics.memory_impact += memory_impact
            
            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, 'prometheus_metrics'):
                self.prometheus_metrics['function_calls'].labels(function=func_name).inc()
                self.prometheus_metrics['function_duration'].labels(function=func_name).observe(duration)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        latest = self.metrics_history[-1]
        
        # System metrics summary
        system_summary = {
            "current": {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "memory_rss_mb": latest.memory_rss_mb,
                "active_threads": latest.active_threads,
                "open_files": latest.open_files,
            }
        }
        
        # Calculate historical averages
        if len(self.metrics_history) > 1:
            metrics_list = list(self.metrics_history)
            system_summary["averages"] = {
                "cpu_percent_1min": sum(m.cpu_percent for m in metrics_list[-60:]) / min(60, len(metrics_list)),
                "memory_percent_1min": sum(m.memory_percent for m in metrics_list[-60:]) / min(60, len(metrics_list)),
                "cpu_percent_5min": sum(m.cpu_percent for m in metrics_list[-300:]) / min(300, len(metrics_list)),
                "memory_percent_5min": sum(m.memory_percent for m in metrics_list[-300:]) / min(300, len(metrics_list)),
            }
        
        # Function performance summary
        func_summary = {}
        for func_name, metrics in self.function_metrics.items():
            if metrics.call_count > 0:
                func_summary[func_name] = {
                    "call_count": metrics.call_count,
                    "avg_time_ms": metrics.avg_time * 1000,
                    "min_time_ms": metrics.min_time * 1000,
                    "max_time_ms": metrics.max_time * 1000,
                    "total_time_s": metrics.total_time,
                    "memory_impact_mb": metrics.memory_impact,
                }
        
        # Performance recommendations
        recommendations = self._generate_recommendations()
        
        return {
            "timestamp": time.time(),
            "system": system_summary,
            "functions": func_summary,
            "recommendations": recommendations,
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        if not self.metrics_history:
            return recommendations
        
        latest = self.metrics_history[-1]
        
        # CPU recommendations
        if latest.cpu_percent > 70:
            recommendations.append("Consider enabling async processing or increasing worker pool size")
        
        # Memory recommendations
        if latest.memory_percent > 80:
            recommendations.append("High memory usage detected - consider implementing memory caching strategies")
        
        # Thread recommendations
        if latest.active_threads > settings.performance.MAX_WORKERS:
            recommendations.append("High thread count - consider using async/await patterns instead of threads")
        
        # Function performance recommendations
        slow_functions = [
            name for name, metrics in self.function_metrics.items()
            if metrics.avg_time > 1.0  # Functions taking more than 1 second on average
        ]
        if slow_functions:
            recommendations.append(f"Slow functions detected: {', '.join(slow_functions[:3])}")
        
        # GC recommendations
        if len(self.metrics_history) > 100:
            recent_gc = [m.gc_collections for m in list(self.metrics_history)[-100:]]
            if len(recent_gc) > 10:
                gen2_collections = sum(gc.get(2, 0) for gc in recent_gc[-10:])
                if gen2_collections > 5:
                    recommendations.append("Frequent GC collections detected - consider object pooling or reducing allocations")
        
        return recommendations


# Global performance monitor instance
performance_monitor = PerformanceMonitor(
    collection_interval=settings.monitoring.METRICS_COLLECTION_INTERVAL
)


def performance_track(func_name: Optional[str] = None):
    """Decorator for tracking function performance."""
    def decorator(func: Callable) -> Callable:
        name = func_name or f"{func.__module__}.{func.__qualname__}"
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with performance_monitor.measure_function(name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with performance_monitor.measure_function(name):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator


def optimize_event_loop() -> None:
    """Optimize the event loop for better performance."""
    if UVLOOP_AVAILABLE and settings.performance.EVENT_LOOP_POLICY == "uvloop":
        try:
            uvloop.install()
            get_logger(__name__).info("uvloop event loop installed for better performance")
        except Exception as e:
            get_logger(__name__).warning(f"Failed to install uvloop: {e}")


def setup_performance_monitoring() -> None:
    """Initialize and start performance monitoring."""
    logger = get_logger(__name__)
    
    # Optimize event loop
    optimize_event_loop()
    
    # Configure garbage collection for better performance
    if settings.performance.GARBAGE_COLLECTION_THRESHOLD > 0:
        gc.set_threshold(settings.performance.GARBAGE_COLLECTION_THRESHOLD, 10, 10)
        logger.info(f"GC threshold set to {settings.performance.GARBAGE_COLLECTION_THRESHOLD}")
    
    # Start performance monitoring in background
    if settings.monitoring.ENABLE_PERFORMANCE_MONITORING:
        # Note: The actual start will happen when the event loop is running
        logger.info("Performance monitoring configured and ready to start")


# Memory optimization utilities
def force_garbage_collection() -> Dict[str, int]:
    """Force garbage collection and return collection counts."""
    before = gc.get_count()
    collected = gc.collect()
    after = gc.get_count()
    
    return {
        "collected": collected,
        "before": before,
        "after": after,
    }


def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage information."""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / 1024 / 1024,
        }
    except Exception as e:
        get_logger(__name__).error(f"Error getting memory usage: {e}")
        return {}


def optimize_memory_usage() -> None:
    """Perform memory optimization operations."""
    logger = get_logger(__name__)
    
    before_memory = get_memory_usage()
    gc_result = force_garbage_collection()
    after_memory = get_memory_usage()
    
    freed_mb = before_memory.get("rss_mb", 0) - after_memory.get("rss_mb", 0)
    
    logger.info(f"Memory optimization completed - freed {freed_mb:.2f}MB, collected {gc_result['collected']} objects")