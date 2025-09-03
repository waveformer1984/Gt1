#!/usr/bin/env python3
"""
Simplified CLI entry point for ballsDeepnit with REZONATE launcher.
This version avoids heavy dependencies that may not be available.
"""

import argparse
import asyncio
import sys
import subprocess
from pathlib import Path


def get_resonate_launcher_path():
    """Get path to the resonate launcher script."""
    # Get the directory where this script is located
    current_dir = Path(__file__).parent.absolute()
    repo_root = current_dir.parent.parent  # Assuming this is in src/ballsdeepnit/
    launcher_path = repo_root / "resonate_launcher.py"
    
    if launcher_path.exists():
        return str(launcher_path)
    
    # Fallback: try to find it in current directory
    launcher_path = Path("resonate_launcher.py")
    if launcher_path.exists():
        return str(launcher_path)
    
    return None


def launch_resonate(action, components=None, verbose=False):
    """Launch REZONATE system using the launcher script."""
    launcher_path = get_resonate_launcher_path()
    
    if not launcher_path:
        print("Error: REZONATE launcher script not found")
        print("Please ensure resonate_launcher.py is in the repository root")
        return False
    
    cmd = ["python3", launcher_path, action]
    
    if components:
        cmd.extend(["--components"] + components)
    
    if verbose:
        cmd.append("--verbose")
    
    try:
        # For start command, we need special handling
        if action == "start":
            print("🎵 Launching REZONATE System...")
            print("Press Ctrl+C to stop the system")
            result = subprocess.run(cmd, cwd=Path(launcher_path).parent)
            return result.returncode == 0
        else:
            result = subprocess.run(cmd, cwd=Path(launcher_path).parent)
            return result.returncode == 0
    except KeyboardInterrupt:
        print("\nREZONATE launch cancelled by user")
        return False
    except Exception as e:
        print(f"Error launching REZONATE: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ballsDeepnit - Advanced AI Framework & REZONATE Project",
        prog="ballsdeepnit"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # REZONATE command
    resonate_parser = subparsers.add_parser(
        "resonate", 
        help="Launch and manage REZONATE modular wearable instrument system"
    )
    resonate_parser.add_argument(
        "action",
        choices=["start", "stop", "status", "restart"],
        help="Action to perform"
    )
    resonate_parser.add_argument(
        "--components",
        nargs="+",
        help="Specific components to start (default: all enabled)"
    )
    resonate_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    # Help command
    help_parser = subparsers.add_parser("help", help="Show help information")
    
    # Info command  
    info_parser = subparsers.add_parser("info", help="Show system information")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "resonate":
        success = launch_resonate(
            action=args.action,
            components=args.components,
            verbose=args.verbose
        )
        if not success:
            sys.exit(1)
    
    elif args.command == "help":
        parser.print_help()
    
    elif args.command == "info":
        print("🍑 ballsDeepnit - Advanced AI Framework")
        print("=" * 50)
        print("🎵 REZONATE - Modular Wearable Instrument System")
        print("")
        print("Components:")
        print("  • Performance UI - Real-time performance interface")
        print("  • Bluetooth Orchestration - Device discovery and network management")
        print("  • MIDI Mapping - MIDI parameter mapping and DAW integration")
        print("  • Hardware Monitor - Sensor data collection and device health")
        print("  • System Coordinator - Central coordination service")
        print("")
        print("Usage:")
        print("  ballsdeepnit resonate start    # Launch REZONATE system")
        print("  ballsdeepnit resonate status   # Check system status")
        print("  ballsdeepnit resonate stop     # Stop system")
        print("")
        print("For more information, use: ballsdeepnit resonate --help")


if __name__ == "__main__":
    main()