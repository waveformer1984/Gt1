"""
High-performance logging system with structured logging and buffering.
"""

import logging
import logging.handlers
import sys
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import orjson as json  # Faster JSON serialization
except ImportError:
    import json

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

from ..core.config import settings


class PerformanceFilter(logging.Filter):
    """Custom filter to add performance metrics to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Add timestamp with microsecond precision
        record.timestamp_us = int(time.time() * 1_000_000)
        
        # Add performance context if available
        if hasattr(record, 'extra'):
            record.performance = record.extra.get('performance', {})
        else:
            record.performance = {}
        
        return True


class OptimizedJSONFormatter(logging.Formatter):
    """High-performance JSON formatter using orjson."""
    
    def __init__(self, include_extra: bool = True) -> None:
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as optimized JSON."""
        log_data = {
            "timestamp": record.created,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add performance metrics if available
        if hasattr(record, 'performance'):
            log_data["performance"] = record.performance
        
        # Add extra fields if enabled
        if self.include_extra and hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        # Use orjson for faster serialization
        try:
            return json.dumps(log_data).decode('utf-8')
        except (TypeError, ValueError):
            # Fallback to standard JSON if orjson fails
            import json as std_json
            return std_json.dumps(log_data, default=str)


class BufferedHandler(logging.handlers.MemoryHandler):
    """Memory-buffered handler for high-performance logging."""
    
    def __init__(self, capacity: int, target: logging.Handler) -> None:
        super().__init__(capacity=capacity, target=target)
        self.setLevel(logging.DEBUG)
    
    def shouldFlush(self, record: logging.LogRecord) -> bool:
        """Flush on ERROR/CRITICAL or when buffer is full."""
        return (
            record.levelno >= logging.ERROR or
            len(self.buffer) >= self.capacity
        )


@lru_cache(maxsize=32)
def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a cached, performance-optimized logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Optional logging level override
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid reconfiguring if already set up
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = level or settings.monitoring.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Prevent duplicate messages from parent loggers
    logger.propagate = False
    
    # Add performance filter
    perf_filter = PerformanceFilter()
    logger.addFilter(perf_filter)
    
    # Configure handlers based on settings
    if settings.monitoring.ENABLE_STRUCTURED_LOGGING and STRUCTLOG_AVAILABLE:
        _configure_structlog(logger)
    else:
        _configure_standard_logging(logger)
    
    return logger


def _configure_structlog(logger: logging.Logger) -> None:
    """Configure structured logging with structlog."""
    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
    ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logger.level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _configure_standard_logging(logger: logging.Logger) -> None:
    """Configure standard logging with performance optimizations."""
    # Console handler with buffering for better performance
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.DEBUG:
        # Detailed format for development
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%H:%M:%S"
        )
    else:
        # JSON format for production with high performance
        formatter = OptimizedJSONFormatter()
    
    console_handler.setFormatter(formatter)
    
    # Use buffered handler for better performance
    if settings.monitoring.LOG_BUFFER_SIZE > 1:
        buffered_console = BufferedHandler(
            capacity=settings.monitoring.LOG_BUFFER_SIZE,
            target=console_handler
        )
        logger.addHandler(buffered_console)
    else:
        logger.addHandler(console_handler)
    
    # File handler for persistent logs (if logs directory exists)
    if settings.LOGS_DIR.exists():
        log_file = settings.LOGS_DIR / f"{settings.APP_NAME.lower()}.log"
        
        # Rotating file handler to prevent huge log files
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        file_handler.setFormatter(OptimizedJSONFormatter())
        
        # Buffer file writes for better performance
        if settings.monitoring.LOG_BUFFER_SIZE > 1:
            buffered_file = BufferedHandler(
                capacity=settings.monitoring.LOG_BUFFER_SIZE,
                target=file_handler
            )
            logger.addHandler(buffered_file)
        else:
            logger.addHandler(file_handler)


class PerformanceLogger:
    """Specialized logger for performance metrics and profiling."""
    
    def __init__(self) -> None:
        self.logger = get_logger("performance")
        self._start_times: Dict[str, float] = {}
    
    def start_timing(self, operation: str) -> None:
        """Start timing an operation."""
        self._start_times[operation] = time.perf_counter()
    
    def end_timing(self, operation: str, **kwargs: Any) -> float:
        """End timing and log the duration."""
        if operation not in self._start_times:
            self.logger.warning(f"No start time found for operation: {operation}")
            return 0.0
        
        duration = time.perf_counter() - self._start_times.pop(operation)
        
        self.logger.info(
            f"Operation completed: {operation}",
            extra={
                "performance": {
                    "operation": operation,
                    "duration_seconds": duration,
                    "duration_ms": duration * 1000,
                    **kwargs
                }
            }
        )
        
        return duration
    
    def log_memory_usage(self, context: str, **kwargs: Any) -> None:
        """Log current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            self.logger.info(
                f"Memory usage: {context}",
                extra={
                    "performance": {
                        "context": context,
                        "memory_rss_mb": memory_info.rss / 1024 / 1024,
                        "memory_vms_mb": memory_info.vms / 1024 / 1024,
                        "memory_percent": process.memory_percent(),
                        **kwargs
                    }
                }
            )
        except ImportError:
            self.logger.warning("psutil not available for memory monitoring")
    
    def log_metric(self, name: str, value: Union[int, float], unit: str = "", **kwargs: Any) -> None:
        """Log a custom performance metric."""
        self.logger.info(
            f"Metric: {name}",
            extra={
                "performance": {
                    "metric_name": name,
                    "metric_value": value,
                    "metric_unit": unit,
                    **kwargs
                }
            }
        )


# Global performance logger instance
perf_logger = PerformanceLogger()


def timing_decorator(operation_name: Optional[str] = None):
    """Decorator to automatically time function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            perf_logger.start_timing(op_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                perf_logger.end_timing(op_name)
        return wrapper
    return decorator


# Configure root logger on module import
root_logger = get_logger("ballsdeepnit")

# Suppress noisy third-party loggers in production
if not settings.DEBUG:
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)