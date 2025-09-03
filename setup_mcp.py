#!/usr/bin/env python3
"""
MCP Setup Script for BallsDeepnit
Comprehensive setup for Model Context Protocol with per-function optimization.
"""

import os
import sys
import subprocess
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MCPSetupManager:
    """Manages the complete MCP setup process."""
    
    def __init__(self):
        self.workspace_root = Path.cwd()
        self.venv_path = self.workspace_root / ".venv"
        self.python_path = self.venv_path / "bin" / "python" if os.name != 'nt' else self.venv_path / "Scripts" / "python.exe"
        self.pip_path = self.venv_path / "bin" / "pip" if os.name != 'nt' else self.venv_path / "Scripts" / "pip.exe"
        
    def run_command(self, command: List[str], cwd: Path = None) -> bool:
        """Run a system command and return success status."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.workspace_root,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"✓ Command succeeded: {' '.join(command)}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Command failed: {' '.join(command)}")
            logger.error(f"Error: {e.stderr}")
            return False
    
    def check_node_installed(self) -> bool:
        """Check if Node.js is installed."""
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✓ Node.js found: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        logger.error("✗ Node.js not found. Please install Node.js 18+ for MCP servers.")
        return False
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility."""
        if sys.version_info < (3, 10):
            logger.error(f"✗ Python 3.10+ required, found {sys.version_info.major}.{sys.version_info.minor}")
            return False
        
        logger.info(f"✓ Python version: {sys.version_info.major}.{sys.version_info.minor}")
        return True
    
    def create_virtual_environment(self) -> bool:
        """Create Python virtual environment if it doesn't exist."""
        if self.venv_path.exists():
            logger.info("✓ Virtual environment already exists")
            return True
        
        logger.info("Creating virtual environment...")
        return self.run_command([sys.executable, "-m", "venv", str(self.venv_path)])
    
    def install_python_dependencies(self) -> bool:
        """Install Python dependencies including MCP packages."""
        logger.info("Installing Python dependencies...")
        
        # Upgrade pip first
        if not self.run_command([str(self.pip_path), "install", "--upgrade", "pip"]):
            return False
        
        # Install core dependencies
        dependencies = [
            # MCP dependencies
            "mcp>=1.0.0",
            "httpx>=0.27.0",
            "anyio>=4.0.0",
            
            # Core framework dependencies
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.5.0",
            "pydantic-settings>=2.1.0",
            "click>=8.0.0",
            "python-dotenv>=1.0.0",
            
            # Performance dependencies
            "uvloop>=0.19.0; sys_platform != 'win32'",
            "orjson>=3.9.0",
            "redis>=5.0.0",
            "diskcache>=5.6.0",
            "psutil>=5.9.0",
            
            # Audio dependencies
            "sounddevice>=0.4.6",
            "numpy>=1.24.0",
            "python-rtmidi>=1.5.0",
            
            # Optional dependencies for extended functionality
            "aiofiles>=23.0.0",
            "watchdog>=3.0.0",
            "structlog>=23.2.0"
        ]
        
        for dep in dependencies:
            if not self.run_command([str(self.pip_path), "install", dep]):
                logger.warning(f"Failed to install {dep}, continuing...")
        
        return True
    
    def install_mcp_servers(self) -> bool:
        """Install official MCP servers via npm."""
        if not self.check_node_installed():
            logger.warning("Skipping MCP server installation - Node.js not available")
            return True
        
        logger.info("Installing MCP servers...")
        
        servers = [
            "@modelcontextprotocol/server-filesystem",
            "@modelcontextprotocol/server-brave-search",
            "@modelcontextprotocol/server-github",
            "@modelcontextprotocol/server-sqlite"
        ]
        
        success = True
        for server in servers:
            if not self.run_command(["npm", "install", "-g", server]):
                logger.warning(f"Failed to install {server}")
                success = False
        
        return success
    
    def create_mcp_configuration(self) -> bool:
        """Create MCP configuration files."""
        logger.info("Creating MCP configuration...")
        
        # Create .env file if it doesn't exist
        env_file = self.workspace_root / ".env"
        if not env_file.exists():
            env_content = """
# MCP Configuration
ENABLE_MCP=true
MCP_MAX_CONNECTIONS=10
MCP_CACHE_TTL=300

# API Keys (add your actual keys)
BRAVE_API_KEY=your_brave_search_api_key_here
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_api_key_here

# Performance Settings
MAX_WORKERS=8
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_REDIS_CACHE=false
REDIS_URL=redis://localhost:6379/0

# Audio Settings
AUDIO_SAMPLE_RATE=44100
AUDIO_BUFFER_SIZE=1024

# Security Settings
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=60
"""
            
            with open(env_file, 'w') as f:
                f.write(env_content.strip())
            
            logger.info("✓ Created .env configuration file")
        else:
            logger.info("✓ .env file already exists")
        
        # Create MCP server configurations directory
        mcp_config_dir = self.workspace_root / "mcp_configs"
        mcp_config_dir.mkdir(exist_ok=True)
        
        # Filesystem server config
        filesystem_config = {
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", str(self.workspace_root)],
            "function_types": ["file_operations"],
            "timeout": 30.0,
            "cache_ttl": 600,
            "priority": 2
        }
        
        # Web search server config
        websearch_config = {
            "name": "web_search",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": {"BRAVE_API_KEY": "${BRAVE_API_KEY}"},
            "function_types": ["api_calls", "real_time_data"],
            "timeout": 15.0,
            "cache_ttl": 300,
            "priority": 3
        }
        
        # GitHub server config
        github_config = {
            "name": "github",
            "command": "npx", 
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"},
            "function_types": ["api_calls", "file_operations"],
            "timeout": 20.0,
            "cache_ttl": 300,
            "priority": 2
        }
        
        # Database server config
        database_config = {
            "name": "database",
            "command": str(self.python_path),
            "args": ["-m", "ballsdeepnit.core.mcp_servers", "database_queries"],
            "function_types": ["database_queries"],
            "timeout": 45.0,
            "cache_ttl": 900,
            "priority": 1
        }
        
        # Audio server config
        audio_config = {
            "name": "audio_processing",
            "command": str(self.python_path),
            "args": ["-m", "ballsdeepnit.core.mcp_servers", "audio_processing"],
            "function_types": ["audio_processing"],
            "timeout": 60.0,
            "cache_ttl": 0,
            "priority": 3
        }
        
        configs = {
            "filesystem.json": filesystem_config,
            "websearch.json": websearch_config,
            "github.json": github_config,
            "database.json": database_config,
            "audio.json": audio_config
        }
        
        for filename, config in configs.items():
            config_file = mcp_config_dir / filename
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"✓ Created {filename}")
        
        return True
    
    def create_startup_scripts(self) -> bool:
        """Create convenience startup scripts."""
        logger.info("Creating startup scripts...")
        
        # Unix script
        if os.name != 'nt':
            script_content = f"""#!/bin/bash
# BallsDeepnit MCP Framework Startup Script

export PYTHONPATH="{self.workspace_root}/src:$PYTHONPATH"

echo "🍑 Starting BallsDeepnit Framework with MCP..."

# Activate virtual environment
source {self.venv_path}/bin/activate

# Check MCP status first
echo "Checking MCP status..."
python -m ballsdeepnit.cli mcp status

# Start the main framework
echo "Starting framework..."
python -m ballsdeepnit.cli run --enable-mcp "$@"
"""
            
            script_path = self.workspace_root / "start_ballsdeepnit.sh"
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Make executable
            os.chmod(script_path, 0o755)
            logger.info("✓ Created start_ballsdeepnit.sh")
        
        # Windows script
        script_content_win = f"""@echo off
REM BallsDeepnit MCP Framework Startup Script

set PYTHONPATH={self.workspace_root}\\src;%PYTHONPATH%

echo 🍑 Starting BallsDeepnit Framework with MCP...

REM Activate virtual environment
call {self.venv_path}\\Scripts\\activate.bat

REM Check MCP status first
echo Checking MCP status...
python -m ballsdeepnit.cli mcp status

REM Start the main framework
echo Starting framework...
python -m ballsdeepnit.cli run --enable-mcp %*
"""
        
        script_path_win = self.workspace_root / "start_ballsdeepnit.bat"
        with open(script_path_win, 'w') as f:
            f.write(script_content_win)
        
        logger.info("✓ Created start_ballsdeepnit.bat")
        
        return True
    
    def create_test_scripts(self) -> bool:
        """Create test scripts for MCP functionality."""
        logger.info("Creating test scripts...")
        
        test_script = f"""#!/usr/bin/env python3
'''
MCP Test Suite for BallsDeepnit
Run comprehensive tests of MCP functionality.
'''

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_mcp_framework():
    '''Test MCP framework functionality.'''
    print("🧪 Testing MCP Framework...")
    
    try:
        from ballsdeepnit.core.framework import framework_context
        
        async with framework_context() as framework:
            print("✓ Framework initialized successfully")
            
            # Test MCP status
            status = await framework.get_mcp_status()
            mcp_status = {
                'enabled': status.get('mcp_enabled'),
                'servers': status.get('servers_count', 0)
            }
            print(f"✓ MCP Status: {mcp_status}")
            
            # Test capabilities
            capabilities = framework.get_available_capabilities()
            print(f"✓ Available capabilities: {{len(capabilities)}} agents")
            
            # Test file operations
            try:
                result = await framework.execute_task(
                    "create_directory",
                    "file_operations",
                    {{"directory_path": "test_mcp_output"}}
                )
                print("✓ File operations test passed")
            except Exception as e:
                print(f"⚠ File operations test failed: {{e}}")
            
            print("🎉 MCP Framework tests completed!")
            
    except Exception as e:
        print(f"❌ MCP Framework test failed: {{e}}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mcp_framework())
    sys.exit(0 if success else 1)
"""
        
        test_path = self.workspace_root / "test_mcp.py"
        with open(test_path, 'w') as f:
            f.write(test_script)
        
        if os.name != 'nt':
            os.chmod(test_path, 0o755)
        
        logger.info("✓ Created test_mcp.py")
        return True
    
    def run_tests(self) -> bool:
        """Run basic MCP functionality tests."""
        logger.info("Running MCP tests...")
        
        # Test Python imports
        try:
            import ballsdeepnit.core.mcp_manager
            import ballsdeepnit.core.framework
            logger.info("✓ Python imports successful")
        except ImportError as e:
            logger.error(f"✗ Import error: {e}")
            return False
        
        # Test CLI commands
        cli_commands = [
            [str(self.python_path), "-m", "ballsdeepnit.cli", "--help"],
            [str(self.python_path), "-m", "ballsdeepnit.cli", "mcp", "--help"]
        ]
        
        for cmd in cli_commands:
            if not self.run_command(cmd):
                logger.error(f"CLI test failed: {' '.join(cmd)}")
                return False
        
        logger.info("✓ Basic tests passed")
        return True
    
    def setup(self) -> bool:
        """Run the complete MCP setup process."""
        logger.info("🍑 Starting BallsDeepnit MCP Setup...")
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Installing Python dependencies", self.install_python_dependencies),
            ("Installing MCP servers", self.install_mcp_servers),
            ("Creating MCP configuration", self.create_mcp_configuration),
            ("Creating startup scripts", self.create_startup_scripts),
            ("Creating test scripts", self.create_test_scripts),
            ("Running basic tests", self.run_tests)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔧 {step_name}...")
            logger.info(f"{'='*60}")
            
            if not step_func():
                logger.error(f"❌ Setup failed at: {step_name}")
                return False
            
            logger.info(f"✅ {step_name} completed successfully")
        
        logger.info(f"\n{'='*60}")
        logger.info("🎉 MCP Setup Complete!")
        logger.info(f"{'='*60}")
        logger.info("\nNext steps:")
        logger.info("1. Update .env file with your API keys")
        logger.info("2. Run: ./start_ballsdeepnit.sh (Unix) or start_ballsdeepnit.bat (Windows)")
        logger.info("3. Test MCP: python -m ballsdeepnit.cli mcp status")
        logger.info("4. Test capabilities: python -m ballsdeepnit.cli mcp capabilities")
        logger.info("5. Run tests: python test_mcp.py")
        
        return True


def main():
    """Main setup function."""
    setup_manager = MCPSetupManager()
    
    try:
        success = setup_manager.setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Setup cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()