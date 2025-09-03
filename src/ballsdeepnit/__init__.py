"""
ballsDeepnit - The Deepest, Most Savage Bot Framework in the Game

High-performance, modular Python automation platform with:
- Zero-downtime hot reload
- Async-first architecture for maximum throughput
- Memory-optimized plugin system
- Real-time performance monitoring
"""

__version__ = "0.1.0"
__author__ = "ballsDeepnit Team"

# Lazy imports for faster startup times
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core.framework import BallsDeepnitFramework
    from .core.plugin_manager import PluginManager
    from .dashboard.app import DashboardApp

# Performance-critical imports
from .core.config import settings
from .utils.logging import get_logger

logger = get_logger(__name__)

# Only import heavy modules when actually needed
def get_framework() -> "BallsDeepnitFramework":
    """Lazy-load the main framework to improve startup time."""
    from .core.framework import BallsDeepnitFramework
    return BallsDeepnitFramework()

def get_plugin_manager() -> "PluginManager":
    """Lazy-load the plugin manager."""
    from .core.plugin_manager import PluginManager
    return PluginManager()

def get_dashboard() -> "DashboardApp":
    """Lazy-load the dashboard application."""
    from .dashboard.app import DashboardApp
    return DashboardApp()

# Performance monitoring setup
if settings.monitoring.ENABLE_PERFORMANCE_MONITORING:
    from .monitoring.performance import setup_performance_monitoring
    setup_performance_monitoring()

__all__ = [
    "__version__",
    "__author__", 
    "settings",
    "get_framework",
    "get_plugin_manager", 
    "get_dashboard",
    "logger",
]