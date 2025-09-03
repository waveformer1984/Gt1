"""
High-performance dashboard components for ballsDeepnit.
"""

# Lazy imports for heavy FastAPI components
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app import DashboardApp

__all__ = [
    "get_dashboard_app",
]

def get_dashboard_app() -> "DashboardApp":
    """Lazy-load the dashboard application."""
    from .app import DashboardApp
    return DashboardApp()