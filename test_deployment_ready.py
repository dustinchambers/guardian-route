#!/usr/bin/env python3
"""
Test if Guardian Route is ready for deployment.

Checks that all required files and data exist.
"""

from pathlib import Path
import sys

print("="*60)
print("DEPLOYMENT READINESS CHECK")
print("="*60)

project_root = Path(__file__).parent
all_checks_passed = True

# Required files check
required_files = {
    "App": "app.py",
    "Dockerfile": "Dockerfile",
    "Railway Config": "railway.json",
    "Web Requirements": "requirements-web.txt",
    "Crime Data": "data/raw/crime_raw.csv",
    "Spatial Grid": "data/processed/spatial_grid.geojson",
    "Filtered Crime": "data/processed/crime_filtered.csv",
    "Triplets": "data/processed/crime_triplets.pkl",
    "Model": "models/trained/cynet_model.pkl",
    "Model Metadata": "models/trained/model_metadata.json",
    "Street Network": "data/network/denver_network.graphml",
    "Tile Mapping": "data/network/tile_edge_mapping.pkl",
    "Streamlit Config": ".streamlit/config.toml"
}

print("\nChecking required files...")
print("-"*60)

for name, filepath in required_files.items():
    full_path = project_root / filepath
    if full_path.exists():
        size = full_path.stat().st_size
        size_mb = size / (1024 * 1024)
        print(f"✓ {name:<20} {filepath:<40} ({size_mb:.1f} MB)")
    else:
        print(f"✗ {name:<20} {filepath:<40} MISSING!")
        all_checks_passed = False

# Check Python dependencies
print("\n" + "-"*60)
print("Checking Python dependencies...")
print("-"*60)

required_packages = [
    "streamlit",
    "streamlit_folium",
    "folium",
    "geopandas",
    "osmnx",
    "pandas",
    "joblib"
]

for package in required_packages:
    try:
        __import__(package)
        print(f"✓ {package}")
    except ImportError:
        print(f"✗ {package} - NOT INSTALLED")
        all_checks_passed = False

# Size check
print("\n" + "-"*60)
print("Checking data sizes...")
print("-"*60)

large_files = [
    ("data/raw/crime_raw.csv", 10),  # Min 10 MB
    ("models/trained/cynet_model.pkl", 0.1),  # Min 0.1 MB
    ("data/network/denver_network.graphml", 1),  # Min 1 MB
]

for filepath, min_mb in large_files:
    full_path = project_root / filepath
    if full_path.exists():
        size_mb = full_path.stat().st_size / (1024 * 1024)
        if size_mb >= min_mb:
            print(f"✓ {filepath:<50} {size_mb:.1f} MB")
        else:
            print(f"⚠ {filepath:<50} {size_mb:.1f} MB (expected >{min_mb} MB)")
            all_checks_passed = False
    else:
        print(f"✗ {filepath:<50} MISSING")
        all_checks_passed = False

# Summary
print("\n" + "="*60)
if all_checks_passed:
    print("✅ DEPLOYMENT READY!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Test locally: streamlit run app.py")
    print("  2. Follow RAILWAY_DEPLOY.md for deployment")
    print("  3. Deploy to Railway: https://railway.app")
    sys.exit(0)
else:
    print("❌ NOT READY FOR DEPLOYMENT")
    print("="*60)
    print("\nIssues found. Please:")
    print("  1. Run missing scripts from the data pipeline")
    print("  2. Install missing dependencies: pip install -r requirements-web.txt")
    print("  3. Check RAILWAY_DEPLOY.md for detailed steps")
    sys.exit(1)
