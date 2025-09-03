#!/usr/bin/env python3
"""
🚀 Hydi Master Setup Script
Complete setup for auto-launch, icons, and platform configuration
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HydiSetup:
    """Master setup orchestrator for Hydi ecosystem"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        
    def check_dependencies(self):
        """Check if required dependencies are available"""
        logger.info("🔍 Checking dependencies...")
        
        missing_deps = []
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error(f"Python 3.8+ required, got {sys.version}")
            return False
        
        # Check for pip
        try:
            subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            missing_deps.append('pip')
        
        # Optional: Check for Pillow
        try:
            import PIL
            logger.info("✅ Pillow available for high-quality icons")
        except ImportError:
            logger.warning("⚠️  Pillow not found - will use SVG fallbacks")
            logger.info("   Install with: pip install Pillow")
        
        if missing_deps:
            logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
            return False
        
        logger.info("✅ Dependencies check passed")
        return True
    
    def setup_auto_launch(self):
        """Configure auto-launch for the current platform"""
        logger.info("🚀 Setting up auto-launch...")
        
        try:
            auto_launch_script = self.script_dir / "auto_launch_setup.py"
            result = subprocess.run([sys.executable, str(auto_launch_script)], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Auto-launch configured successfully")
                return True
            else:
                logger.error(f"❌ Auto-launch setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Auto-launch setup error: {e}")
            return False
    
    def generate_icons(self):
        """Generate icons for all platforms"""
        logger.info("🎨 Generating icons...")
        
        try:
            icon_script = self.script_dir / "icon_generator.py"
            result = subprocess.run([sys.executable, str(icon_script)], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Icons generated successfully")
                print(result.stdout)  # Show icon generator output
                return True
            else:
                logger.error(f"❌ Icon generation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Icon generation error: {e}")
            return False
    
    def setup_mobile(self):
        """Setup mobile app dependencies"""
        logger.info("📱 Setting up mobile app...")
        
        mobile_dir = self.project_root / "mobile" / "hydi-mobile"
        if not mobile_dir.exists():
            logger.warning("⚠️  Mobile directory not found, skipping mobile setup")
            return True
        
        try:
            # Check if npm/yarn is available
            package_manager = "npm"
            try:
                subprocess.run(["yarn", "--version"], check=True, capture_output=True)
                package_manager = "yarn"
                logger.info("📦 Using Yarn for mobile dependencies")
            except:
                try:
                    subprocess.run(["npm", "--version"], check=True, capture_output=True)
                    logger.info("📦 Using npm for mobile dependencies")
                except:
                    logger.warning("⚠️  No package manager found, skipping mobile dependencies")
                    return True
            
            # Install mobile dependencies
            os.chdir(mobile_dir)
            if package_manager == "yarn":
                result = subprocess.run(["yarn", "install"], capture_output=True, text=True)
            else:
                result = subprocess.run(["npm", "install"], capture_output=True, text=True)
            
            os.chdir(self.project_root)  # Return to project root
            
            if result.returncode == 0:
                logger.info("✅ Mobile dependencies installed")
                return True
            else:
                logger.warning(f"⚠️  Mobile dependency installation issues: {result.stderr}")
                return True  # Non-critical
                
        except Exception as e:
            logger.warning(f"⚠️  Mobile setup warning: {e}")
            return True  # Non-critical
    
    def install_python_dependencies(self):
        """Install Python dependencies if needed"""
        logger.info("🐍 Checking Python dependencies...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            logger.info("📋 No requirements.txt found, skipping Python deps")
            return True
        
        try:
            # Check if virtual environment exists
            venv_path = self.project_root / ".venv"
            if venv_path.exists():
                logger.info("📦 Virtual environment found")
                
                # Activate venv and install deps
                if sys.platform == "win32":
                    pip_path = venv_path / "Scripts" / "pip"
                else:
                    pip_path = venv_path / "bin" / "pip"
                
                if pip_path.exists():
                    result = subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        logger.info("✅ Python dependencies updated")
                        return True
            else:
                logger.info("💡 Consider creating a virtual environment: python -m venv .venv")
            
            # Fallback to system pip
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Python dependencies installed")
                return True
            else:
                logger.warning(f"⚠️  Python dependency installation issues: {result.stderr}")
                return True  # Non-critical
                
        except Exception as e:
            logger.warning(f"⚠️  Python dependency warning: {e}")
            return True  # Non-critical
    
    def create_desktop_shortcuts(self):
        """Create desktop shortcuts and menu entries"""
        logger.info("🔗 Creating desktop shortcuts...")
        
        # This is handled by the icon generator, but we can add additional shortcuts
        shortcuts_created = []
        
        desktop_path = Path.home() / "Desktop"
        if not desktop_path.exists():
            desktop_path = Path.home()
        
        # Create a comprehensive launcher script
        launcher_script = self.project_root / "launch_hydi_complete.py"
        launcher_content = f'''#!/usr/bin/env python3
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
        print("\\n🛑 Stopping Hydi services...")
        backend_proc.terminate()
        try:
            dashboard_proc.terminate()
        except:
            pass

if __name__ == "__main__":
    main()
'''
        
        with open(launcher_script, 'w') as f:
            f.write(launcher_content)
        
        os.chmod(launcher_script, 0o755)
        shortcuts_created.append(str(launcher_script))
        
        logger.info(f"✅ Created launcher: {launcher_script}")
        return True
    
    def verify_setup(self):
        """Verify that setup completed successfully"""
        logger.info("🔍 Verifying setup...")
        
        checks = []
        
        # Check icons
        icon_dir = self.project_root / "assets" / "icons"
        if icon_dir.exists() and any(icon_dir.iterdir()):
            checks.append("Icons: ✅")
        else:
            checks.append("Icons: ❌")
        
        # Check auto-launch scripts
        scripts_dir = self.project_root / "scripts"
        startup_scripts = list(scripts_dir.glob("hydi_startup.*"))
        if startup_scripts:
            checks.append("Auto-launch: ✅")
        else:
            checks.append("Auto-launch: ❌")
        
        # Check mobile config
        mobile_config = self.project_root / "mobile" / "hydi-mobile" / "app.json"
        if mobile_config.exists():
            checks.append("Mobile config: ✅")
        else:
            checks.append("Mobile config: ⚠️")
        
        logger.info("📋 Setup verification:")
        for check in checks:
            logger.info(f"   {check}")
        
        return all("✅" in check for check in checks[:2])  # Icons and auto-launch are critical
    
    def run_setup(self, skip_mobile=False, skip_autolaunch=False, skip_icons=False):
        """Run complete setup process"""
        logger.info("🚀 Starting Hydi Complete Setup")
        logger.info("=" * 50)
        
        success_count = 0
        total_steps = 6
        
        # Step 1: Check dependencies
        if self.check_dependencies():
            success_count += 1
        
        # Step 2: Install Python dependencies
        if self.install_python_dependencies():
            success_count += 1
        
        # Step 3: Generate icons
        if not skip_icons and self.generate_icons():
            success_count += 1
        elif skip_icons:
            logger.info("⏭️  Skipped icon generation")
            success_count += 1
        
        # Step 4: Setup auto-launch
        if not skip_autolaunch and self.setup_auto_launch():
            success_count += 1
        elif skip_autolaunch:
            logger.info("⏭️  Skipped auto-launch setup")
            success_count += 1
        
        # Step 5: Setup mobile
        if not skip_mobile and self.setup_mobile():
            success_count += 1
        elif skip_mobile:
            logger.info("⏭️  Skipped mobile setup")
            success_count += 1
        
        # Step 6: Create shortcuts
        if self.create_desktop_shortcuts():
            success_count += 1
        
        # Verification
        setup_success = self.verify_setup()
        
        logger.info("\n" + "=" * 50)
        logger.info(f"🎉 Setup completed: {success_count}/{total_steps} steps successful")
        
        if success_count == total_steps and setup_success:
            logger.info("✅ Hydi is ready to use!")
            logger.info("💡 Tips:")
            logger.info("   - Restart your computer to test auto-launch")
            logger.info("   - Check Desktop for Hydi shortcuts")
            logger.info("   - Run 'python launch_hydi_complete.py' to start manually")
            return True
        else:
            logger.warning("⚠️  Setup completed with some issues")
            logger.info("💡 You can re-run this script to fix any issues")
            return False

def main():
    """Main entry point with CLI options"""
    parser = argparse.ArgumentParser(description="Hydi Complete Setup")
    parser.add_argument("--skip-mobile", action="store_true", 
                       help="Skip mobile app setup")
    parser.add_argument("--skip-autolaunch", action="store_true", 
                       help="Skip auto-launch configuration")
    parser.add_argument("--skip-icons", action="store_true", 
                       help="Skip icon generation")
    parser.add_argument("--verify-only", action="store_true", 
                       help="Only verify existing setup")
    
    args = parser.parse_args()
    
    setup = HydiSetup()
    
    if args.verify_only:
        logger.info("🔍 Verification mode")
        success = setup.verify_setup()
        return 0 if success else 1
    
    success = setup.run_setup(
        skip_mobile=args.skip_mobile,
        skip_autolaunch=args.skip_autolaunch,
        skip_icons=args.skip_icons
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())