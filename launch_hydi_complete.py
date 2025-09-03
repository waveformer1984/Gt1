#!/usr/bin/env python3
"""
🧠 Hydi Complete Launcher
Launch all Hydi components with one click
"""

import sys
import subprocess
import time
import os
from pathlib import Path

def main():
    print("🧠 Starting Hydi AI Framework...")
    
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Start backend
    print("🚀 Starting backend...")
    backend_proc = subprocess.Popen([sys.executable, "-m", "ballsdeepnit.cli"])
    
    # Wait a moment
    time.sleep(3)
    
    # Start dashboard if available
    dashboard_path = project_root / "src" / "ballsdeepnit" / "dashboard" / "dashboard.py"
    if dashboard_path.exists():
        print("🌐 Starting dashboard...")
        dashboard_proc = subprocess.Popen([sys.executable, str(dashboard_path)])
    
    print("✅ Hydi AI Framework started!")
    print("🌐 Dashboard: http://localhost:5000")
    print("🔗 API: http://localhost:8000")
    print("💡 Press Ctrl+C to stop all services")
    
    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping Hydi services...")
        backend_proc.terminate()
        try:
            dashboard_proc.terminate()
        except:
            pass

if __name__ == "__main__":
    main()
