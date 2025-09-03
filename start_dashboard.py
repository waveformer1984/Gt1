#!/usr/bin/env python3
"""
Z-areo OBD2 Dashboard Startup Script
====================================

This script starts the web dashboard for the Z-areo OBD2 system.
"""

import sys
import uvicorn
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def start_dashboard():
    """Start the Z-areo OBD2 dashboard."""
    print("Starting Z-areo OBD2 Dashboard...")
    print("=" * 50)
    print("Dashboard will be available at:")
    print("  • Main Interface: http://localhost:8765")
    print("  • API Documentation: http://localhost:8765/docs")
    print("  • Authentication: http://localhost:8765/api/auth/login")
    print("  • OBD2 API: http://localhost:8765/api/obd2/status")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print()

    try:
        uvicorn.run(
            "src.ballsdeepnit.dashboard.app:app",
            host="0.0.0.0",
            port=8765,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nDashboard stopped by user")
    except Exception as e:
        print(f"\nError starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_dashboard()