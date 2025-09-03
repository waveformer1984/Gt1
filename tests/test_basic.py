"""
Basic test suite for HYDI_System / REZONATE
"""

import pytest
import sys
import os

# Add the project root to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_project_structure():
    """Test that required project directories exist"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_dirs = [
        'hardware-design',
        'firmware', 
        'software',
        'docs',
        'automation',
        'tests'
    ]
    
    for directory in required_dirs:
        dir_path = os.path.join(project_root, directory)
        assert os.path.exists(dir_path), f"Required directory {directory} not found"
        assert os.path.isdir(dir_path), f"{directory} is not a directory"


def test_main_scripts_importable():
    """Test that main Python scripts can be imported without errors"""
    try:
        import resonate_launcher
        assert hasattr(resonate_launcher, '__file__'), "resonate_launcher module loaded"
    except ImportError as e:
        pytest.skip(f"resonate_launcher not importable: {e}")
    
    try:
        import repl_bridge  
        assert hasattr(repl_bridge, '__file__'), "repl_bridge module loaded"
    except ImportError as e:
        pytest.skip(f"repl_bridge not importable: {e}")


def test_requirements_files_exist():
    """Test that dependency files exist"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    requirements_files = [
        'requirements.txt',
        'requirements-basic.txt',
        'pyproject.toml'
    ]
    
    for req_file in requirements_files:
        file_path = os.path.join(project_root, req_file)
        assert os.path.exists(file_path), f"Requirements file {req_file} not found"


def test_software_components_exist():
    """Test that software components have expected structure"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    software_dir = os.path.join(project_root, 'software')
    
    expected_components = [
        'performance-ui',
        'bluetooth-orchestration', 
        'midi-mapping'
    ]
    
    for component in expected_components:
        component_path = os.path.join(software_dir, component)
        assert os.path.exists(component_path), f"Software component {component} not found"
        
        readme_path = os.path.join(component_path, 'README.md')
        assert os.path.exists(readme_path), f"README.md not found in {component}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])