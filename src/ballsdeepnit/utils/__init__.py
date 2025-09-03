"""
Utility modules for ballsDeepnit with performance optimizations.
"""

# Fast imports for commonly used utilities
from .logging import get_logger, perf_logger, timing_decorator

__all__ = [
    "get_logger",
    "perf_logger", 
    "timing_decorator",
]