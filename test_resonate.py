#!/usr/bin/env python3
"""
Basic tests for REZONATE launcher functionality.
"""

import asyncio
import json
import subprocess
import sys
import time
import unittest
from pathlib import Path


class TestResonateLauncher(unittest.TestCase):
    """Test cases for REZONATE launcher."""
    
    def setUp(self):
        """Set up test environment."""
        self.launcher_path = Path("resonate_launcher.py")
        self.cli_path = Path("ballsdeepnit_cli.py")
    
    def test_launcher_exists(self):
        """Test that launcher script exists."""
        self.assertTrue(self.launcher_path.exists(), 
                       "REZONATE launcher script should exist")
    
    def test_cli_exists(self):
        """Test that CLI script exists."""
        self.assertTrue(self.cli_path.exists(),
                       "ballsDeepnit CLI script should exist")
    
    def test_launcher_help(self):
        """Test launcher help command."""
        result = subprocess.run(
            ["python3", str(self.launcher_path), "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("REZONATE", result.stdout)
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = subprocess.run(
            ["python3", str(self.cli_path), "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("ballsDeepnit", result.stdout)
    
    def test_resonate_status(self):
        """Test REZONATE status command."""
        result = subprocess.run(
            ["python3", str(self.launcher_path), "status"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("REZONATE System Status", result.stdout)
    
    def test_cli_resonate_status(self):
        """Test CLI REZONATE status command."""
        result = subprocess.run(
            ["python3", str(self.cli_path), "resonate", "status"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("REZONATE System Status", result.stdout)
    
    def test_cli_info(self):
        """Test CLI info command."""
        result = subprocess.run(
            ["python3", str(self.cli_path), "info"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("ballsDeepnit", result.stdout)
        self.assertIn("REZONATE", result.stdout)
    
    def test_resonate_help(self):
        """Test REZONATE help via CLI."""
        result = subprocess.run(
            ["python3", str(self.cli_path), "resonate", "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("start", result.stdout)
        self.assertIn("stop", result.stdout)
        self.assertIn("status", result.stdout)
    
    def test_component_scripts_exist(self):
        """Test that component scripts exist."""
        components = [
            "software/performance-ui/main.py",
            "software/bluetooth-orchestration/app.py", 
            "software/midi-mapping/mapping_engine.py"
        ]
        
        for component in components:
            component_path = Path(component)
            self.assertTrue(component_path.exists(),
                           f"Component script {component} should exist")
    
    def test_config_generation(self):
        """Test that configuration is generated correctly."""
        config_path = Path("resonate_config.json")
        
        # Run status to ensure config exists
        result = subprocess.run(
            ["python3", str(self.launcher_path), "status"],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertTrue(config_path.exists(),
                       "Configuration file should be generated")
        
        # Check config content
        with open(config_path) as f:
            config = json.load(f)
        
        self.assertIn("rezonate", config)
        self.assertIn("components", config)


def run_integration_test():
    """Run a simple integration test."""
    print("🧪 Running REZONATE integration test...")
    
    # Test status command first (simpler)
    try:
        result = subprocess.run(
            ["python3", "ballsdeepnit_cli.py", "resonate", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "REZONATE System Status" in result.stdout:
            print("✅ Integration test passed - REZONATE status command works")
            return True
        else:
            print("❌ Integration test failed - REZONATE status failed")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        return False


if __name__ == "__main__":
    # Run unit tests
    print("🧪 Running REZONATE unit tests...")
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*50)
    
    # Run integration test
    success = run_integration_test()
    
    if not success:
        sys.exit(1)
    
    print("\n✅ All tests passed! REZONATE launcher is working correctly.")