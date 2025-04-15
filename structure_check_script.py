#!/usr/bin/env python3
"""
Script to verify and fix the project structure.
"""

import os
import sys
from pathlib import Path
import shutil

def check_file(path, create=False, content=""):
    """Check if a file exists and optionally create it."""
    if os.path.exists(path):
        print(f"✅ Found: {path}")
        return True
    else:
        print(f"❌ Missing: {path}")
        if create:
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as f:
                    f.write(content)
                print(f"  Created: {path}")
                return True
            except Exception as e:
                print(f"  Error creating {path}: {e}")
                return False
        return False

def check_structure():
    """Check the project structure."""
    # Get the project root (the directory containing this script)
    project_root = os.path.abspath(os.path.dirname(__file__))
    print(f"Project root: {project_root}")

    # Check key directories
    directories = [
        "cmmc_tracker",
        "cmmc_tracker/app",
        "cmmc_tracker/app/models",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/functional",
        "cmmc_tracker/app/routes",
        "cmmc_tracker/app/services",
        "cmmc_tracker/app/utils",
        "cmmc_tracker/app/templates",
        "cmmc_tracker/app/static",
    ]

    for directory in directories:
        dir_path = os.path.join(project_root, directory)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"✅ Found directory: {directory}")
        else:
            print(f"❌ Missing directory: {directory}")
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"  Created directory: {directory}")
            except Exception as e:
                print(f"  Error creating directory {directory}: {e}")

    # Check key files
    files = [
        ("cmmc_tracker/__init__.py", ""),
        ("cmmc_tracker/app/__init__.py", ""),
        ("cmmc_tracker/app/models/__init__.py", ""),
        ("cmmc_tracker/app/routes/__init__.py", ""),
        ("cmmc_tracker/app/services/__init__.py", ""),
        ("cmmc_tracker/app/utils/__init__.py", ""),
        ("cmmc_tracker/run.py", ""),
        ("cmmc_tracker/config.py", ""),
        ("Dockerfile", ""),
        ("docker-compose.yml", ""),
        ("requirements.txt", ""),
        ("tests/__init__.py", ""),
        ("tests/unit/__init__.py", ""),
        ("tests/integration/__init__.py", ""),
        ("tests/functional/__init__.py", ""),
        ("tests/conftest.py", ""),
        ("pytest.ini", ""),
        (".coveragerc", ""),
    ]

    for file_path, _ in files:
        check_file(os.path.join(project_root, file_path))

    # Print out the directory structure
    print("\nDirectory structure:")
    for root, dirs, files in os.walk(project_root):
        level = root.replace(project_root, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            if not file.startswith('.'):  # Skip hidden files
                print(f"{sub_indent}{file}")

if __name__ == "__main__":
    check_structure()