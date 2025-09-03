#!/usr/bin/env python3
"""
🧠 Hydi Auto-Launch Setup
Advanced startup configuration for cross-platform auto-launch
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoLaunchManager:
    """Manages auto-launch configuration across platforms"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        self.app_name = "HydiAI"
        self.app_description = "Hydi Advanced AI REPL & Automation Framework"
        
    def setup_auto_launch(self):
        """Set up auto-launch based on the current platform"""
        logger.info(f"Setting up auto-launch for {self.system}")
        
        if self.system == "windows":
            return self._setup_windows_autostart()
        elif self.system == "darwin":  # macOS
            return self._setup_macos_autostart()
        elif self.system == "linux":
            return self._setup_linux_autostart()
        else:
            logger.error(f"Unsupported platform: {self.system}")
            return False
    
    def _setup_windows_autostart(self):
        """Configure Windows startup via registry and startup folder"""
        try:
            import winreg
            
            # Create the startup script
            startup_script = self._create_windows_startup_script()
            
            # Add to Windows startup folder
            startup_folder = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"))
            startup_link = startup_folder / f"{self.app_name}.bat"
            
            shutil.copy2(startup_script, startup_link)
            logger.info(f"Added startup script to: {startup_link}")
            
            # Also add to registry for more reliable startup
            reg_key = winreg.HKEY_CURRENT_USER
            reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            
            with winreg.OpenKey(reg_key, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, str(startup_script))
            
            logger.info("Added registry entry for auto-launch")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Windows autostart: {e}")
            return False
    
    def _setup_macos_autostart(self):
        """Configure macOS launch agent"""
        try:
            # Create launch agent plist
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(exist_ok=True)
            
            plist_file = launch_agents_dir / f"com.ballsdeepnit.{self.app_name.lower()}.plist"
            startup_script = self._create_macos_startup_script()
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ballsdeepnit.{self.app_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{startup_script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>{Path.home()}/Library/Logs/{self.app_name}.out</string>
    <key>StandardErrorPath</key>
    <string>{Path.home()}/Library/Logs/{self.app_name}.err</string>
</dict>
</plist>"""
            
            with open(plist_file, 'w') as f:
                f.write(plist_content)
            
            # Load the launch agent
            subprocess.run(['launchctl', 'load', str(plist_file)], check=True)
            logger.info(f"Created and loaded launch agent: {plist_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup macOS autostart: {e}")
            return False
    
    def _setup_linux_autostart(self):
        """Configure Linux autostart via .desktop file"""
        try:
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = autostart_dir / f"{self.app_name}.desktop"
            startup_script = self._create_linux_startup_script()
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Comment={self.app_description}
Exec={startup_script}
Icon={self.project_root}/assets/icons/hydi_icon.png
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
X-KDE-autostart-after=panel
StartupNotify=true
"""
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            # Make executable
            os.chmod(desktop_file, 0o755)
            logger.info(f"Created autostart entry: {desktop_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Linux autostart: {e}")
            return False
    
    def _create_windows_startup_script(self):
        """Create Windows batch startup script"""
        script_path = self.project_root / "scripts" / "hydi_startup.bat"
        script_path.parent.mkdir(exist_ok=True)
        
        script_content = f"""@echo off
REM Hydi Auto-Launch Script for Windows
REM Generated by auto_launch_setup.py

cd /d "{self.project_root}"

REM Check if Python environment exists
if exist ".venv\\Scripts\\activate.bat" (
    call .venv\\Scripts\\activate.bat
) else (
    echo Virtual environment not found, using system Python
)

REM Start Hydi backend
start "Hydi Backend" /min python -m ballsdeepnit.cli

REM Wait a moment for backend to start
timeout /t 5 /nobreak >nul

REM Start dashboard if available
if exist "src\\ballsdeepnit\\dashboard\\dashboard.py" (
    start "Hydi Dashboard" /min python src\\ballsdeepnit\\dashboard\\dashboard.py
)

REM Create system tray notification
echo Hydi AI Framework started successfully!
"""
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        return script_path
    
    def _create_macos_startup_script(self):
        """Create macOS shell startup script"""
        script_path = self.project_root / "scripts" / "hydi_startup.sh"
        script_path.parent.mkdir(exist_ok=True)
        
        script_content = f"""#!/bin/bash
# Hydi Auto-Launch Script for macOS
# Generated by auto_launch_setup.py

cd "{self.project_root}"

# Activate virtual environment if available
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start Hydi backend
nohup python -m ballsdeepnit.cli > /tmp/hydi_backend.log 2>&1 &

# Wait for backend to start
sleep 5

# Start dashboard if available
if [ -f "src/ballsdeepnit/dashboard/dashboard.py" ]; then
    nohup python src/ballsdeepnit/dashboard/dashboard.py > /tmp/hydi_dashboard.log 2>&1 &
fi

# Send notification
osascript -e 'display notification "Hydi AI Framework started successfully!" with title "Hydi"'
"""
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        return script_path
    
    def _create_linux_startup_script(self):
        """Create Linux shell startup script"""
        script_path = self.project_root / "scripts" / "hydi_startup.sh"
        script_path.parent.mkdir(exist_ok=True)
        
        script_content = f"""#!/bin/bash
# Hydi Auto-Launch Script for Linux
# Generated by auto_launch_setup.py

cd "{self.project_root}"

# Activate virtual environment if available
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Start Hydi backend
nohup python -m ballsdeepnit.cli > /tmp/hydi_backend.log 2>&1 &

# Wait for backend to start
sleep 5

# Start dashboard if available
if [ -f "src/ballsdeepnit/dashboard/dashboard.py" ]; then
    nohup python src/ballsdeepnit/dashboard/dashboard.py > /tmp/hydi_dashboard.log 2>&1 &
fi

# Send notification if notify-send is available
if command -v notify-send &> /dev/null; then
    notify-send "Hydi" "AI Framework started successfully!"
fi
"""
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(script_path, 0o755)
        return script_path
    
    def remove_auto_launch(self):
        """Remove auto-launch configuration"""
        logger.info(f"Removing auto-launch for {self.system}")
        
        try:
            if self.system == "windows":
                # Remove from registry
                import winreg
                reg_key = winreg.HKEY_CURRENT_USER
                reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
                
                with winreg.OpenKey(reg_key, reg_path, 0, winreg.KEY_SET_VALUE) as key:
                    try:
                        winreg.DeleteValue(key, self.app_name)
                    except FileNotFoundError:
                        pass
                
                # Remove from startup folder
                startup_folder = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"))
                startup_link = startup_folder / f"{self.app_name}.bat"
                if startup_link.exists():
                    startup_link.unlink()
                
            elif self.system == "darwin":
                # Remove launch agent
                launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
                plist_file = launch_agents_dir / f"com.ballsdeepnit.{self.app_name.lower()}.plist"
                
                if plist_file.exists():
                    subprocess.run(['launchctl', 'unload', str(plist_file)], check=False)
                    plist_file.unlink()
                
            elif self.system == "linux":
                # Remove autostart desktop file
                autostart_dir = Path.home() / ".config" / "autostart"
                desktop_file = autostart_dir / f"{self.app_name}.desktop"
                if desktop_file.exists():
                    desktop_file.unlink()
            
            logger.info("Auto-launch removed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove auto-launch: {e}")
            return False

def main():
    """Main entry point"""
    print("🧠 Hydi Auto-Launch Setup")
    print("=" * 40)
    
    manager = AutoLaunchManager()
    
    if len(sys.argv) > 1 and sys.argv[1] == "remove":
        success = manager.remove_auto_launch()
        action = "removed"
    else:
        success = manager.setup_auto_launch()
        action = "configured"
    
    if success:
        print(f"✅ Auto-launch {action} successfully!")
        print(f"🎯 Hydi will now start automatically on system boot")
        if action == "configured":
            print("💡 To remove auto-launch, run: python auto_launch_setup.py remove")
    else:
        print(f"❌ Failed to {action.rstrip('d')} auto-launch")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())