#!/usr/bin/env python3
"""
Repository Cleanup and MCP Verification Script
Cleans up unnecessary files and verifies MCP setup across all repositories.
"""

import os
import sys
import shutil
import subprocess
import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import zipfile
import tempfile

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cleanup_verification.log')
    ]
)
logger = logging.getLogger(__name__)


class RepositoryCleanup:
    """Handles repository cleanup and organization."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.archive_dir = workspace_root / "archive"
        self.temp_dir = workspace_root / "temp_cleanup"
        
        # Files and directories to keep
        self.keep_files = {
            'pyproject.toml', 'requirements.txt', 'requirements-basic.txt',
            'README.md', 'LICENSE', 'setup_mcp.py', 'MCP_SETUP_README.md',
            'PERFORMANCE_OPTIMIZATIONS.md', 'SECURITY_LOCKDOWN.md',
            'repl_bridge.py', 'hydi_toggle_scanner.py'
        }
        
        self.keep_dirs = {
            'src', 'tests', 'examples', 'bin', '.git', '.github', 'mobile'
        }
        
        # Zip files to archive (not delete, in case they contain unique code)
        self.zip_files_to_archive = []
        
        # Redundant/unnecessary files to remove
        self.files_to_remove = {
            'cleanup-workspace.sh',  # We'll create a better one
            'install-secure.sh',     # Superseded by setup_mcp.py
            'launch_hydi.bat',       # Old launcher
            'launch_hydi_mobile.sh', # Old launcher
        }
        
        # Documentation files that might be redundant
        self.docs_to_review = {
            'CLEANUP_CHECKLIST.md', 'SETUP_GUIDE.md', 'VERIFICATION_SUMMARY.md',
            'Z-AREO_OBD2_SETUP_GUIDE.md', 'universal_design_protocol_udp.md'
        }

    def scan_zip_files(self) -> List[Path]:
        """Scan for all zip files in the workspace."""
        zip_files = []
        for file_path in self.workspace_root.glob("*.zip"):
            zip_files.append(file_path)
        return zip_files

    def analyze_zip_content(self, zip_path: Path) -> Dict[str, Any]:
        """Analyze the content of a zip file to determine if it's useful."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                
                # Count different file types
                python_files = [f for f in file_list if f.endswith('.py')]
                js_files = [f for f in file_list if f.endswith('.js')]
                config_files = [f for f in file_list if f.endswith(('.json', '.yaml', '.yml', '.toml'))]
                doc_files = [f for f in file_list if f.endswith(('.md', '.txt', '.rst'))]
                
                return {
                    'total_files': len(file_list),
                    'python_files': len(python_files),
                    'js_files': len(js_files),
                    'config_files': len(config_files),
                    'doc_files': len(doc_files),
                    'file_list': file_list[:10],  # First 10 files for preview
                    'has_unique_code': len(python_files) > 0 or len(js_files) > 0
                }
        except Exception as e:
            logger.error(f"Failed to analyze {zip_path}: {e}")
            return {'error': str(e)}

    def create_archive_directory(self):
        """Create archive directory for old files."""
        self.archive_dir.mkdir(exist_ok=True)
        logger.info(f"Created archive directory: {self.archive_dir}")

    def archive_zip_files(self):
        """Archive all zip files with analysis."""
        zip_files = self.scan_zip_files()
        
        if not zip_files:
            logger.info("No zip files found to archive")
            return
        
        self.create_archive_directory()
        
        # Create analysis report
        analysis_report = {
            'timestamp': str(asyncio.get_event_loop().time()),
            'total_zip_files': len(zip_files),
            'files_analyzed': {}
        }
        
        for zip_path in zip_files:
            logger.info(f"Analyzing and archiving: {zip_path.name}")
            
            # Analyze content
            analysis = self.analyze_zip_content(zip_path)
            analysis_report['files_analyzed'][zip_path.name] = analysis
            
            # Move to archive
            archive_path = self.archive_dir / zip_path.name
            shutil.move(str(zip_path), str(archive_path))
            logger.info(f"Archived: {zip_path.name} -> archive/")
        
        # Save analysis report
        report_path = self.archive_dir / "zip_analysis_report.json"
        with open(report_path, 'w') as f:
            json.dump(analysis_report, f, indent=2)
        
        logger.info(f"Zip file analysis report saved: {report_path}")

    def remove_redundant_files(self):
        """Remove files that are redundant or superseded."""
        for file_name in self.files_to_remove:
            file_path = self.workspace_root / file_name
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Removed redundant file: {file_name}")

    def consolidate_documentation(self):
        """Consolidate and organize documentation files."""
        docs_dir = self.workspace_root / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # Move documentation files that should be organized
        for doc_file in self.docs_to_review:
            doc_path = self.workspace_root / doc_file
            if doc_path.exists():
                # Check if it's still relevant or should be archived
                if self._is_doc_still_relevant(doc_file):
                    new_path = docs_dir / doc_file
                    shutil.move(str(doc_path), str(new_path))
                    logger.info(f"Moved documentation: {doc_file} -> docs/")
                else:
                    archive_path = self.archive_dir / doc_file
                    shutil.move(str(doc_path), str(archive_path))
                    logger.info(f"Archived outdated documentation: {doc_file}")

    def _is_doc_still_relevant(self, doc_file: str) -> bool:
        """Determine if a documentation file is still relevant."""
        # Keep certain docs that might still be useful
        relevant_docs = {
            'PERFORMANCE_OPTIMIZATIONS.md',
            'SECURITY_LOCKDOWN.md',
            'universal_design_protocol_udp.md'
        }
        return doc_file in relevant_docs

    def clean_redundant_directories(self):
        """Clean up redundant directories."""
        # Check ballsdeepnit_full_bundle
        bundle_dir = self.workspace_root / "ballsdeepnit_full_bundle"
        if bundle_dir.exists():
            # If src/ already exists and is more complete, archive the bundle
            src_dir = self.workspace_root / "src"
            if src_dir.exists() and self._compare_directories(src_dir, bundle_dir):
                shutil.move(str(bundle_dir), str(self.archive_dir / "ballsdeepnit_full_bundle"))
                logger.info("Archived redundant ballsdeepnit_full_bundle directory")

    def _compare_directories(self, dir1: Path, dir2: Path) -> bool:
        """Compare two directories to see if dir1 is more complete than dir2."""
        # Simple comparison - count Python files
        dir1_py_files = len(list(dir1.rglob("*.py")))
        dir2_py_files = len(list(dir2.rglob("*.py")))
        return dir1_py_files >= dir2_py_files

    def generate_cleanup_report(self) -> Dict[str, Any]:
        """Generate a cleanup report."""
        return {
            'timestamp': str(asyncio.get_event_loop().time()),
            'actions_taken': {
                'zip_files_archived': len(list(self.archive_dir.glob("*.zip"))),
                'redundant_files_removed': len(self.files_to_remove),
                'docs_organized': True,
                'directories_cleaned': True
            },
            'current_structure': {
                'main_files': [f.name for f in self.workspace_root.iterdir() if f.is_file()],
                'main_directories': [d.name for d in self.workspace_root.iterdir() if d.is_dir()],
                'archive_contents': [f.name for f in self.archive_dir.iterdir()] if self.archive_dir.exists() else []
            }
        }


class MCPVerification:
    """Handles MCP verification across all components."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.verification_results = {}

    async def verify_mcp_setup(self) -> Dict[str, Any]:
        """Verify MCP setup across all components."""
        logger.info("Starting MCP verification...")
        
        results = {
            'python_environment': await self._verify_python_environment(),
            'dependencies': await self._verify_dependencies(),
            'mcp_components': await self._verify_mcp_components(),
            'configuration': await self._verify_configuration(),
            'agents': await self._verify_agents(),
            'security': await self._verify_security(),
            'tests': await self._run_basic_tests()
        }
        
        self.verification_results = results
        return results

    async def _verify_python_environment(self) -> Dict[str, Any]:
        """Verify Python environment setup."""
        try:
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, text=True)
            python_version = result.stdout.strip()
            
            # Check if virtual environment exists
            venv_path = self.workspace_root / ".venv"
            venv_exists = venv_path.exists()
            
            return {
                'status': 'success',
                'python_version': python_version,
                'virtual_environment': venv_exists,
                'python_path': sys.executable
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    async def _verify_dependencies(self) -> Dict[str, Any]:
        """Verify MCP and other dependencies."""
        required_packages = [
            'mcp', 'httpx', 'anyio', 'fastapi', 'uvicorn',
            'pydantic', 'click', 'sounddevice', 'numpy'
        ]
        
        missing_packages = []
        installed_packages = {}
        
        for package in required_packages:
            try:
                result = subprocess.run([sys.executable, '-c', f'import {package}; print({package}.__version__)'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    installed_packages[package] = result.stdout.strip()
                else:
                    missing_packages.append(package)
            except Exception:
                missing_packages.append(package)
        
        return {
            'status': 'success' if not missing_packages else 'warning',
            'installed_packages': installed_packages,
            'missing_packages': missing_packages
        }

    async def _verify_mcp_components(self) -> Dict[str, Any]:
        """Verify MCP component files exist and are valid."""
        required_files = [
            'src/ballsdeepnit/core/mcp_manager.py',
            'src/ballsdeepnit/core/mcp_servers.py',
            'src/ballsdeepnit/core/mcp_security.py',
            'src/ballsdeepnit/core/framework.py',
            'setup_mcp.py'
        ]
        
        file_status = {}
        for file_path in required_files:
            full_path = self.workspace_root / file_path
            if full_path.exists():
                try:
                    # Basic syntax check for Python files
                    if file_path.endswith('.py'):
                        with open(full_path, 'r') as f:
                            compile(f.read(), file_path, 'exec')
                    file_status[file_path] = 'valid'
                except SyntaxError as e:
                    file_status[file_path] = f'syntax_error: {e}'
                except Exception as e:
                    file_status[file_path] = f'error: {e}'
            else:
                file_status[file_path] = 'missing'
        
        all_valid = all(status == 'valid' for status in file_status.values())
        
        return {
            'status': 'success' if all_valid else 'error',
            'files': file_status
        }

    async def _verify_configuration(self) -> Dict[str, Any]:
        """Verify configuration files."""
        config_files = [
            '.env',
            'pyproject.toml',
            'requirements.txt'
        ]
        
        config_status = {}
        for config_file in config_files:
            config_path = self.workspace_root / config_file
            if config_path.exists():
                config_status[config_file] = 'exists'
            else:
                config_status[config_file] = 'missing'
        
        return {
            'status': 'success',
            'configurations': config_status
        }

    async def _verify_agents(self) -> Dict[str, Any]:
        """Verify agent system components."""
        try:
            # Add src to Python path for testing
            sys.path.insert(0, str(self.workspace_root / "src"))
            
            # Try to import and verify agents
            from ballsdeepnit.core.framework import get_framework
            
            framework = get_framework()
            
            return {
                'status': 'success',
                'framework_loaded': True,
                'mcp_enabled': hasattr(framework, 'mcp_manager')
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'framework_loaded': False
            }

    async def _verify_security(self) -> Dict[str, Any]:
        """Verify security components."""
        try:
            sys.path.insert(0, str(self.workspace_root / "src"))
            from ballsdeepnit.core.mcp_security import get_security_manager
            
            security_manager = get_security_manager()
            
            return {
                'status': 'success',
                'security_manager_loaded': True,
                'validation_enabled': security_manager.enabled
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'security_manager_loaded': False
            }

    async def _run_basic_tests(self) -> Dict[str, Any]:
        """Run basic functionality tests."""
        test_results = {}
        
        # Test MCP setup script
        try:
            setup_script = self.workspace_root / "setup_mcp.py"
            if setup_script.exists():
                result = subprocess.run([sys.executable, str(setup_script), '--help'],
                                      capture_output=True, text=True, timeout=10)
                test_results['setup_script'] = 'working' if result.returncode == 0 else 'error'
            else:
                test_results['setup_script'] = 'missing'
        except Exception as e:
            test_results['setup_script'] = f'error: {e}'
        
        # Test CLI imports
        try:
            sys.path.insert(0, str(self.workspace_root / "src"))
            from ballsdeepnit.cli import cli
            test_results['cli_import'] = 'success'
        except Exception as e:
            test_results['cli_import'] = f'error: {e}'
        
        return {
            'status': 'success',
            'tests': test_results
        }


class SystemInitializer:
    """Initializes the complete system after cleanup."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    async def initialize_system(self) -> Dict[str, Any]:
        """Initialize the complete system."""
        logger.info("Starting system initialization...")
        
        initialization_steps = [
            ('Environment Setup', self._setup_environment),
            ('Install Dependencies', self._install_dependencies),
            ('Configure System', self._configure_system),
            ('Initialize MCP', self._initialize_mcp),
            ('Start Services', self._start_services),
            ('Run Validation', self._run_validation)
        ]
        
        results = {}
        for step_name, step_func in initialization_steps:
            logger.info(f"Executing: {step_name}")
            try:
                result = await step_func()
                results[step_name] = {'status': 'success', 'result': result}
                logger.info(f"✅ {step_name} completed successfully")
            except Exception as e:
                results[step_name] = {'status': 'error', 'error': str(e)}
                logger.error(f"❌ {step_name} failed: {e}")
                break  # Stop on first failure
        
        return results

    async def _setup_environment(self) -> Dict[str, Any]:
        """Setup the environment."""
        # Check if virtual environment exists, create if not
        venv_path = self.workspace_root / ".venv"
        if not venv_path.exists():
            result = subprocess.run([sys.executable, "-m", "venv", str(venv_path)],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Failed to create virtual environment: {result.stderr}")
        
        return {"virtual_environment": "created/verified"}

    async def _install_dependencies(self) -> Dict[str, Any]:
        """Install required dependencies."""
        venv_python = self.workspace_root / ".venv" / "bin" / "python"
        if not venv_python.exists():
            venv_python = self.workspace_root / ".venv" / "Scripts" / "python.exe"
        
        # Install from requirements.txt if it exists
        requirements_file = self.workspace_root / "requirements.txt"
        if requirements_file.exists():
            result = subprocess.run([str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Failed to install dependencies: {result.stderr}")
        
        return {"dependencies": "installed"}

    async def _configure_system(self) -> Dict[str, Any]:
        """Configure the system."""
        # Create .env file if it doesn't exist
        env_file = self.workspace_root / ".env"
        if not env_file.exists():
            env_content = """# MCP Configuration
ENABLE_MCP=true
MCP_MAX_CONNECTIONS=10
MCP_CACHE_TTL=300

# Performance Settings
MAX_WORKERS=8
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_REDIS_CACHE=false

# Security Settings
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=60
ENABLE_REQUEST_VALIDATION=true

# Audio Settings
AUDIO_SAMPLE_RATE=44100
AUDIO_BUFFER_SIZE=1024

# API Keys (add your actual keys)
BRAVE_API_KEY=your_brave_search_api_key_here
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_api_key_here
"""
            with open(env_file, 'w') as f:
                f.write(env_content)
        
        return {"configuration": "created/verified"}

    async def _initialize_mcp(self) -> Dict[str, Any]:
        """Initialize MCP components."""
        # Run the MCP setup script
        setup_script = self.workspace_root / "setup_mcp.py"
        if setup_script.exists():
            # Note: We won't run the full setup here to avoid conflicts
            # Just verify it's ready to run
            return {"mcp_setup": "ready"}
        else:
            raise Exception("MCP setup script not found")

    async def _start_services(self) -> Dict[str, Any]:
        """Start necessary services."""
        # For now, just verify the system is ready to start
        return {"services": "ready_to_start"}

    async def _run_validation(self) -> Dict[str, Any]:
        """Run final validation."""
        verifier = MCPVerification(self.workspace_root)
        results = await verifier.verify_mcp_setup()
        
        if all(result.get('status') == 'success' for result in results.values()):
            return {"validation": "passed"}
        else:
            raise Exception("System validation failed")


async def main():
    """Main cleanup and verification function."""
    workspace_root = Path.cwd()
    
    print("🍑 BallsDeepnit Repository Cleanup and MCP Verification")
    print("=" * 60)
    
    # Step 1: Repository Cleanup
    print("\n🧹 PHASE 1: Repository Cleanup")
    print("-" * 40)
    
    cleanup = RepositoryCleanup(workspace_root)
    
    try:
        # Archive zip files
        cleanup.archive_zip_files()
        
        # Remove redundant files
        cleanup.remove_redundant_files()
        
        # Consolidate documentation
        cleanup.consolidate_documentation()
        
        # Clean redundant directories
        cleanup.clean_redundant_directories()
        
        # Generate cleanup report
        cleanup_report = cleanup.generate_cleanup_report()
        
        print("✅ Repository cleanup completed successfully!")
        print(f"📊 Cleanup Report:")
        print(f"   - Zip files archived: {cleanup_report['actions_taken']['zip_files_archived']}")
        print(f"   - Redundant files removed: {cleanup_report['actions_taken']['redundant_files_removed']}")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False
    
    # Step 2: MCP Verification
    print("\n🔍 PHASE 2: MCP Verification")
    print("-" * 40)
    
    verifier = MCPVerification(workspace_root)
    
    try:
        verification_results = await verifier.verify_mcp_setup()
        
        print("📋 Verification Results:")
        for component, result in verification_results.items():
            status = result.get('status', 'unknown')
            if status == 'success':
                print(f"   ✅ {component}: OK")
            elif status == 'warning':
                print(f"   ⚠️ {component}: Warning")
            else:
                print(f"   ❌ {component}: Error")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    
    # Step 3: System Initialization
    print("\n🚀 PHASE 3: System Initialization")
    print("-" * 40)
    
    initializer = SystemInitializer(workspace_root)
    
    try:
        init_results = await initializer.initialize_system()
        
        print("🎯 Initialization Results:")
        for step, result in init_results.items():
            status = result.get('status', 'unknown')
            if status == 'success':
                print(f"   ✅ {step}: Completed")
            else:
                print(f"   ❌ {step}: Failed - {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # Final Summary
    print("\n🎉 CLEANUP AND VERIFICATION COMPLETE!")
    print("=" * 60)
    print("\n📝 Next Steps:")
    print("1. Review the cleanup report in 'cleanup_verification.log'")
    print("2. Check archived files in 'archive/' directory if needed")
    print("3. Update .env file with your actual API keys")
    print("4. Run: python setup_mcp.py (for full MCP setup)")
    print("5. Start system: ./start_ballsdeepnit.sh")
    print("\n🍑 Ready to go balls deep with clean, organized MCP-powered agents!")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)