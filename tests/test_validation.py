"""Simple validation tests for CI."""

import sys
import os
from pathlib import Path

def test_python_version():
    """Test Python version is 3.9+."""
    assert sys.version_info >= (3, 9)

def test_project_structure():
    """Test basic project structure exists."""
    project_root = Path(__file__).parent.parent
    
    # Check directories
    assert (project_root / "src").exists()
    assert (project_root / "tests").exists()
    
    # Check files
    assert (project_root / "README.md").exists()
    assert (project_root / "pyproject.toml").exists()

def test_basic_file_existence():
    """Test that basic files exist."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    # Check main files exist
    expected_files = ["cli.py", "smart_cli.py"]
    for file_name in expected_files:
        file_path = src_dir / file_name
        assert file_path.exists(), f"{file_name} should exist in src/"

def test_environment():
    """Test environment is set up correctly."""
    # Python should be available
    assert sys.executable
    
    # Basic modules should work
    import json
    import datetime
    assert json is not None
    assert datetime is not None