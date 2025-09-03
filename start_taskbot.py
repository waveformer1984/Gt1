#!/usr/bin/env python3
"""
TaskBot System Launcher
======================

Simple script to start the TaskBot system with all components.
"""

import asyncio
import argparse
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def start_api_server():
    """Start the TaskBot API server."""
    print("🚀 Starting TaskBot API server...")
    try:
        result = subprocess.Popen([
            sys.executable, "-m", "src.ballsdeepnit.dashboard.task_bot_api"
        ], cwd=Path(__file__).parent)
        
        # Give the server time to start
        time.sleep(3)
        print("✅ TaskBot API server started on http://localhost:8001")
        return result
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def open_dashboard():
    """Open the web dashboard in the default browser."""
    dashboard_path = Path(__file__).parent / "task_bot_dashboard.html"
    if dashboard_path.exists():
        print("🌐 Opening TaskBot Dashboard...")
        webbrowser.open(f"file://{dashboard_path.absolute()}")
        print("✅ Dashboard opened in your default browser")
        print("💡 Make sure to set API base URL to: http://localhost:8001/api/taskbot")
    else:
        print("❌ Dashboard file not found")

def run_demo():
    """Run the TaskBot demonstration."""
    print("🎯 Running TaskBot demonstration...")
    try:
        subprocess.run([sys.executable, "task_bot_demo.py"], 
                      cwd=Path(__file__).parent, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Demo failed: {e}")
    except FileNotFoundError:
        print("❌ Demo script not found")

def show_status():
    """Show system status using CLI."""
    print("📊 Checking TaskBot system status...")
    try:
        subprocess.run([sys.executable, "task_bot_cli.py", "status"], 
                      cwd=Path(__file__).parent, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Status check failed: {e}")
    except FileNotFoundError:
        print("❌ CLI script not found")

def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(
        description="TaskBot System Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available modes:
  full     - Start API server and open dashboard (default)
  api      - Start only the API server
  demo     - Run the demonstration
  status   - Check system status
  help     - Show CLI help

Examples:
  python start_taskbot.py              # Start full system
  python start_taskbot.py demo         # Run demo
  python start_taskbot.py status       # Check status
        """
    )
    
    parser.add_argument('mode', nargs='?', default='full',
                       choices=['full', 'api', 'demo', 'status', 'help'],
                       help='Launch mode (default: full)')
    
    parser.add_argument('--no-browser', action='store_true',
                       help='Don\'t open browser automatically')
    
    args = parser.parse_args()
    
    print("🤖 TaskBot System Launcher")
    print("=" * 50)
    
    if args.mode == 'help':
        print("\n📚 TaskBot CLI Help:")
        try:
            subprocess.run([sys.executable, "task_bot_cli.py", "--help"], 
                          cwd=Path(__file__).parent)
        except FileNotFoundError:
            print("❌ CLI script not found")
        return
    
    if args.mode == 'demo':
        run_demo()
        return
    
    if args.mode == 'status':
        show_status()
        return
    
    if args.mode in ['full', 'api']:
        # Start API server
        api_process = start_api_server()
        
        if api_process is None:
            print("❌ Failed to start API server")
            return
        
        if args.mode == 'full' and not args.no_browser:
            time.sleep(2)  # Give API more time to fully start
            open_dashboard()
        
        try:
            print("\n🎛️  TaskBot System Running")
            print("-" * 30)
            print("API Server: http://localhost:8001")
            print("Dashboard: task_bot_dashboard.html")
            print("CLI: python task_bot_cli.py --help")
            print("\nPress Ctrl+C to stop...")
            
            # Keep the script running
            api_process.wait()
            
        except KeyboardInterrupt:
            print("\n⚠️  Shutting down TaskBot system...")
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_process.kill()
            print("👋 TaskBot system stopped")

if __name__ == "__main__":
    main()