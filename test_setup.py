#!/usr/bin/env python3
"""
Guardian Route - Setup Verification Test

Quick test to verify environment and dependencies.
"""

import sys
from pathlib import Path

print("="*60)
print("GUARDIAN ROUTE - SETUP VERIFICATION")
print("="*60)

# Track results
tests_passed = 0
tests_failed = 0

def test(name, func):
    """Run a test function."""
    global tests_passed, tests_failed
    try:
        func()
        print(f"✓ {name}")
        tests_passed += 1
        return True
    except Exception as e:
        print(f"✗ {name}: {e}")
        tests_failed += 1
        return False

# Test 1: Python version
def check_python_version():
    version = sys.version_info
    if version.major != 3 or version.minor < 9:
        raise Exception(f"Python 3.9+ required, got {version.major}.{version.minor}")

test("Python version (3.9+)", check_python_version)

# Test 2: Core dependencies
def check_pandas():
    import pandas

test("pandas", check_pandas)

def check_numpy():
    import numpy

test("numpy", check_numpy)

def check_geopandas():
    import geopandas

test("geopandas", check_geopandas)

def check_shapely():
    import shapely

test("shapely", check_shapely)

def check_osmnx():
    import osmnx

test("osmnx", check_osmnx)

def check_matplotlib():
    import matplotlib

test("matplotlib", check_matplotlib)

def check_folium():
    import folium

test("folium", check_folium)

def check_joblib():
    import joblib

test("joblib", check_joblib)

# Test 3: Cynet (optional)
def check_cynet():
    import cynet

cynet_available = test("cynet (optional)", check_cynet)
if not cynet_available:
    print("  → Cynet not installed (placeholder model will be used)")

# Test 4: Project structure
def check_directories():
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/network",
        "models/trained",
        "scripts/utils",
        "notebooks",
        "outputs/routes"
    ]
    project_root = Path(__file__).parent
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            raise Exception(f"Missing directory: {dir_path}")

test("Project directory structure", check_directories)

# Test 5: Script files
def check_scripts():
    required_scripts = [
        "scripts/01_download_data.py",
        "scripts/02_create_spatial_grid.py",
        "scripts/03_prepare_triplets.py",
        "scripts/04_train_model.py",
        "scripts/utils/spatial.py",
        "scripts/utils/cynet_wrapper.py"
    ]
    project_root = Path(__file__).parent
    for script_path in required_scripts:
        full_path = project_root / script_path
        if not full_path.exists():
            raise Exception(f"Missing script: {script_path}")

test("Required scripts", check_scripts)

# Test 6: Import project utilities
def check_utils_import():
    sys.path.append(str(Path(__file__).parent / "scripts"))
    from utils.spatial import create_spatial_grid, validate_coordinates
    from utils.cynet_wrapper import validate_triplet_format

test("Project utilities import", check_utils_import)

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print(f"Passed: {tests_passed}")
print(f"Failed: {tests_failed}")

if tests_failed == 0:
    print("\n✓ All tests passed! Setup is complete.")
    print("\nNext steps:")
    print("  1. Review TESTING.md for detailed testing guide")
    print("  2. Run: python scripts/01_download_data.py")
    print("  3. Follow the testing guide to validate each component")
else:
    print(f"\n✗ {tests_failed} test(s) failed. Please install missing dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
