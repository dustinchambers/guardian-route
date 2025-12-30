# Guardian Route - Quick Start Guide

Get up and running in 5 minutes.

## Step 1: Setup Environment (2 min)

```bash
# Navigate to project
cd ~/guardian-route

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** If `cynet` installation fails, that's OK! Continue anyway - a placeholder model will be used.

## Step 2: Verify Setup (30 sec)

```bash
# Run setup test
python test_setup.py
```

You should see:
```
✓ Python version (3.9+)
✓ pandas
✓ numpy
✓ geopandas
...
✓ All tests passed! Setup is complete.
```

## Step 3: Run Data Pipeline (2-3 min)

```bash
# Download Denver crime data
python scripts/01_download_data.py
# → Downloads ~100MB CSV, shows stats

# Create spatial grid (1,000ft tiles)
python scripts/02_create_spatial_grid.py
# → Creates grid, filters data, assigns crimes to tiles

# Prepare training data
python scripts/03_prepare_triplets.py
# → Transforms to Cynet format

# Train model
python scripts/04_train_model.py
# → Trains model (or creates placeholder)
```

Each script will show progress and confirm success.

## Step 4: Verify Outputs

```bash
# Check what was created
ls -lh data/raw/
ls -lh data/processed/
ls -lh models/trained/

# Quick data check
python3 << 'EOF'
import pandas as pd
import geopandas as gpd
import pickle

# Check crime data
crime = pd.read_csv('data/processed/crime_filtered.csv')
print(f"✓ Crime records: {len(crime):,}")

# Check grid
grid = gpd.read_file('data/processed/spatial_grid.geojson')
print(f"✓ Grid tiles: {len(grid):,}")

# Check triplet
with open('data/processed/crime_triplets.pkl', 'rb') as f:
    triplet = pickle.load(f)
print(f"✓ Triplet shape: {triplet['timeseries'].shape}")

# Check model
import joblib
model = joblib.load('models/trained/cynet_model.pkl')
print(f"✓ Model loaded: {type(model).__name__}")
EOF
```

## Success! 🎉

You've completed the data pipeline. Next steps:

### Option A: Visual Verification
Create a quick crime heatmap:
```bash
python3 << 'EOF'
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

grid = gpd.read_file('data/processed/spatial_grid.geojson')
crime = pd.read_csv('data/processed/crime_filtered.csv')

counts = crime.groupby('tile_id').size().reset_index(name='crime_count')
grid_with_counts = grid.merge(counts, on='tile_id', how='left').fillna(0)

fig, ax = plt.subplots(figsize=(12, 10))
grid_with_counts.plot(column='crime_count', ax=ax, legend=True,
                       cmap='YlOrRd', edgecolor='gray', linewidth=0.1)
plt.title('Denver Crime Density (2019-2024)')
plt.savefig('crime_heatmap.png', dpi=150, bbox_inches='tight')
print("✓ Saved: crime_heatmap.png")
EOF

open crime_heatmap.png  # View the heatmap
```

### Option B: Continue Implementation
The routing components still need to be built:
- Network preparation script
- Routing utilities
- Interactive notebook

See the detailed implementation plan in:
```bash
cat ~/.claude/plans/memoized-crafting-sloth.md
```

### Option C: Detailed Testing
For comprehensive testing with troubleshooting:
```bash
cat TESTING.md
```

## Common Issues

**"cynet not found"**
→ Expected! Placeholder model will work for testing.

**Download fails**
→ Check internet connection, or download manually:
```bash
curl -o data/raw/crime_raw.csv "https://www.denvergov.org/media/gis/DataCatalog/crime/csv/crime.csv"
```

**"No module named 'utils'"**
→ Scripts must be run from project root:
```bash
cd ~/guardian-route
python scripts/01_download_data.py  # ✓ Correct
```

**Memory error during triplet creation**
→ Reduce time range or tile count in scripts

## What You've Built

- ✅ Data pipeline (download → filter → tessellate → transform)
- ✅ Spatial grid (1,000ft tiles across Denver)
- ✅ Predictive model foundation
- ✅ Training data in Cynet-compatible format

## Next: Routing Integration

To complete the MVP, you need:
1. Download OSMnx street network
2. Create tile-to-edge mapping
3. Build interactive routing notebook

Would you like me to continue implementing these components?
