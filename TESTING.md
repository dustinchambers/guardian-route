# Guardian Route - Testing Guide

This guide walks through testing the Guardian Route MVP incrementally.

## Prerequisites

### 1. Environment Setup

```bash
cd ~/guardian-route

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Note on Cynet**: The `cynet` package may not be available on PyPI. If installation fails:
```bash
# Install without cynet for now
pip install pandas numpy geopandas shapely pyproj osmnx networkx matplotlib seaborn folium joblib scikit-learn jupyter requests tqdm

# Cynet can be installed later from source if needed:
# git clone https://github.com/zeroknowledgediscovery/Cynet
# cd Cynet && pip install -e .
```

### 2. Verify Installation

```bash
python3 -c "import pandas, geopandas, osmnx; print('✓ Core libraries installed')"
```

## Incremental Testing

### Phase 1: Data Pipeline

#### Test 1.1 - Download Crime Data

```bash
# Run data download
python scripts/01_download_data.py
```

**Expected Output:**
- Download progress bar
- File saved to `data/raw/crime_raw.csv`
- Statistics showing:
  - File size (should be 50-200 MB)
  - Total records (500K-1M)
  - Date range (2019-present)
  - Column names including GEO_LON, GEO_LAT, REPORTED_DATE

**Verify:**
```bash
# Check file exists
ls -lh data/raw/crime_raw.csv

# Preview first few rows
head -5 data/raw/crime_raw.csv
```

**Troubleshooting:**
- If download fails: Check internet connection, try manual download from https://www.denvergov.org/media/gis/DataCatalog/crime/csv/crime.csv
- If file is very small (<1MB): The URL may have changed, check Denver Open Data portal

---

#### Test 1.2 - Create Spatial Grid

```bash
# Run grid creation
python scripts/02_create_spatial_grid.py
```

**Expected Output:**
- "Loading filtered data" message
- Coordinate validation (should keep 90%+ of records)
- Grid creation (500-1000 tiles)
- Assignment of crimes to tiles
- Summary statistics by dataset (training/validation)

**Verify:**
```bash
# Check outputs exist
ls -lh data/processed/crime_filtered.csv
ls -lh data/processed/spatial_grid.geojson

# Count filtered records
wc -l data/processed/crime_filtered.csv

# Inspect grid (requires Python)
python3 << EOF
import geopandas as gpd
grid = gpd.read_file('data/processed/spatial_grid.geojson')
print(f"Grid tiles: {len(grid)}")
print(f"Columns: {list(grid.columns)}")
print(grid.head())
EOF
```

**Troubleshooting:**
- "Crime data not found": Run Test 1.1 first
- Very few tiles created: Check coordinate validation - Denver bbox may need adjustment in `utils/spatial.py`
- Low tile assignment rate: Verify coordinates are in Denver area

---

#### Test 1.3 - Prepare Triplets

```bash
# Run triplet preparation
python scripts/03_prepare_triplets.py
```

**Expected Output:**
- Hourly binning statistics
- Matrix creation (tiles × hours)
- Sparsity report (will be high, 80-95% zeros)
- Binary conversion
- Event occurrence rate (1-5%)
- Saved triplet files

**Verify:**
```bash
# Check triplet file
ls -lh data/processed/crime_triplets.pkl

# Inspect triplet structure
python3 << EOF
import pickle
with open('data/processed/crime_triplets.pkl', 'rb') as f:
    triplet = pickle.load(f)
print(f"Tiles: {len(triplet['row_coords'])}")
print(f"Time points: {len(triplet['col_dates'])}")
print(f"Shape: {triplet['timeseries'].shape}")
print(f"Data type: {triplet['timeseries'].dtype}")
print(f"First 5 tiles: {triplet['row_coords'][:5]}")
EOF
```

**Troubleshooting:**
- Out of memory: Reduce time resolution or tile count
- Very sparse matrix (>98% zeros): Expected for crime data, but verify dates are parsing correctly

---

### Phase 2: Model Training

#### Test 2.1 - Train Model

```bash
# Run model training
python scripts/04_train_model.py
```

**Expected Output:**
- Triplet loading confirmation
- Cynet import attempt
  - If successful: Model training progress
  - If failed: Placeholder model creation (this is OK for testing)
- Model saved with metadata

**Verify:**
```bash
# Check model files
ls -lh models/trained/cynet_model.pkl
cat models/trained/model_metadata.json

# Test model loading
python3 << EOF
import joblib
model = joblib.load('models/trained/cynet_model.pkl')
print(f"Model type: {type(model)}")
print(f"Model attributes: {dir(model)}")
EOF
```

**Troubleshooting:**
- Cynet import fails: Expected - placeholder model will be used for testing
- Training crashes: May need to install Cynet from source (see Prerequisites)
- For real predictions: Install Cynet from GitHub

---

## Quick Integration Test

Run all pipeline steps sequentially:

```bash
# Create test script
cat > test_pipeline.sh << 'EOF'
#!/bin/bash
set -e  # Exit on error

echo "==================================="
echo "Guardian Route - Pipeline Test"
echo "==================================="

cd ~/guardian-route
source venv/bin/activate

echo ""
echo "Step 1: Download data..."
python scripts/01_download_data.py

echo ""
echo "Step 2: Create spatial grid..."
python scripts/02_create_spatial_grid.py

echo ""
echo "Step 3: Prepare triplets..."
python scripts/03_prepare_triplets.py

echo ""
echo "Step 4: Train model..."
python scripts/04_train_model.py

echo ""
echo "==================================="
echo "Pipeline test COMPLETE ✓"
echo "==================================="
EOF

chmod +x test_pipeline.sh
./test_pipeline.sh
```

---

## Visual Verification Tests

### Test Grid Visualization

Create a quick visualization to verify the spatial grid:

```python
# Save as test_grid_viz.py
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

# Load grid and crime data
grid = gpd.read_file('data/processed/spatial_grid.geojson')
crime = pd.read_csv('data/processed/crime_filtered.csv')

# Count crimes per tile
crime_counts = crime.groupby('tile_id').size().reset_index(name='count')
grid_with_counts = grid.merge(crime_counts, on='tile_id', how='left').fillna(0)

# Plot
fig, ax = plt.subplots(figsize=(12, 10))
grid_with_counts.plot(column='count', ax=ax, legend=True, cmap='YlOrRd',
                       edgecolor='gray', linewidth=0.1, alpha=0.7)
plt.title('Crime Density by Tile (2019-2024)')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.tight_layout()
plt.savefig('test_grid_visualization.png', dpi=150)
print("Saved: test_grid_visualization.png")
```

Run it:
```bash
python test_grid_viz.py
open test_grid_visualization.png  # macOS
```

---

## Common Issues & Solutions

### Issue: "Module not found"
**Solution:** Activate virtual environment
```bash
source ~/guardian-route/venv/bin/activate
```

### Issue: "Permission denied"
**Solution:** Make scripts executable
```bash
chmod +x scripts/*.py
```

### Issue: Download fails or very slow
**Solution:** Manual download
```bash
cd ~/guardian-route/data/raw
curl -o crime_raw.csv "https://www.denvergov.org/media/gis/DataCatalog/crime/csv/crime.csv"
```

### Issue: Very few valid coordinates
**Solution:** Check Denver bbox in `scripts/utils/spatial.py`
The default bbox is:
```python
DENVER_BBOX = {
    'lat_min': 39.60,
    'lat_max': 39.90,
    'lon_min': -105.12,
    'lon_max': -104.60
}
```

### Issue: Cynet not available
**Solution:** This is expected. The placeholder model allows testing the pipeline. For production:
```bash
# Install from source
cd ~/
git clone https://github.com/zeroknowledgediscovery/Cynet
cd Cynet
pip install -e .
```

---

## Success Criteria

After running all tests, you should have:

✅ `data/raw/crime_raw.csv` (50-200 MB)
✅ `data/processed/crime_filtered.csv` (filtered, with tile_id)
✅ `data/processed/spatial_grid.geojson` (500-1000 tiles)
✅ `data/processed/crime_triplets.pkl` (binary spatiotemporal matrix)
✅ `models/trained/cynet_model.pkl` (trained or placeholder model)
✅ `models/trained/model_metadata.json` (training metadata)

---

## Next Steps After Testing

Once the data pipeline is validated:

1. **Complete routing integration:**
   - Run `scripts/06_prepare_network.py` (to be implemented)
   - This downloads OSMnx network and creates tile-edge mapping

2. **Test routing notebook:**
   - Open `notebooks/02_interactive_routing.ipynb`
   - Run cells to generate safe routes

3. **Validate outputs:**
   - Routes should be exported as GeoJSON
   - Visualization should show risk heatmap + routes

---

## Getting Help

If tests fail consistently:

1. Check error messages in terminal
2. Verify file paths in scripts match your system
3. Review data statistics - ensure reasonable values
4. Check Python version: `python3 --version` (should be 3.10 or 3.11)
5. Verify disk space: `df -h ~/guardian-route`

For Cynet-specific issues, see: https://github.com/zeroknowledgediscovery/Cynet/issues
