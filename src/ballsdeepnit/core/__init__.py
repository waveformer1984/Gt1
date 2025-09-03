"""
Core ballsDeepnit framework components with performance optimizations.
"""

# Performance-optimized lazy imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Settings
    from .framework import BallsDeepnitFramework

# Fast imports for commonly used items
from .config import settings

__all__ = [
    "settings",
]

# Lazy loading functions for heavy modules
def get_framework() -> "BallsDeepnitFramework":
    """Lazy-load the main framework."""
    from .framework import BallsDeepnitFramework
    return BallsDeepnitFramework()