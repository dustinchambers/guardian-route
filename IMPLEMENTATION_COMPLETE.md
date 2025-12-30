# Guardian Route MVP - Implementation Complete! 🎉

## What Was Built

A complete **safety-weighted routing system** for Denver that:
1. Predicts crime risk using Cynet algorithm
2. Generates safer route alternatives
3. Visualizes risk with interactive maps

---

## 📁 Project Structure

```
guardian-route/
├── README.md                    # Project overview
├── QUICKSTART.md                # 5-minute getting started
├── TESTING.md                   # Comprehensive testing guide
├── requirements.txt             # Python dependencies
├── test_setup.py                # Automated setup verification
│
├── data/
│   ├── raw/                     # Downloaded crime data
│   ├── processed/               # Filtered data, grid, triplets
│   └── network/                 # OSMnx network, tile-edge mapping
│
├── models/
│   ├── trained/                 # Cynet model + metadata
│   └── evaluation/              # Validation results
│
├── scripts/
│   ├── 01_download_data.py      # ✅ Download Denver crime CSV
│   ├── 02_create_spatial_grid.py # ✅ Create 1,000ft tiles
│   ├── 03_prepare_triplets.py   # ✅ Transform to Cynet format
│   ├── 04_train_model.py        # ✅ Train predictive model
│   ├── 05_validate_model.py     # ✅ Validate on 2024 data
│   ├── 06_prepare_network.py    # ✅ OSMnx + tile mapping
│   └── utils/
│       ├── spatial.py           # ✅ Spatial operations
│       ├── cynet_wrapper.py     # ✅ Cynet interface
│       └── routing.py           # ✅ Risk-weighted routing
│
├── notebooks/
│   ├── 00_data_exploration.ipynb    # ✅ EDA & visualizations
│   └── 02_interactive_routing.ipynb # ✅ MAIN DELIVERABLE
│
└── outputs/
    └── routes/                  # Generated GeoJSON routes
```

---

## 🚀 Quick Start (5 Minutes)

### 1. Setup Environment
```bash
cd ~/guardian-route
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Verify Setup
```bash
python test_setup.py
```
Expected: `✓ All tests passed!`

### 3. Run Data Pipeline
```bash
python scripts/01_download_data.py       # ~1 min
python scripts/02_create_spatial_grid.py # ~30 sec
python scripts/03_prepare_triplets.py    # ~30 sec
python scripts/04_train_model.py         # ~1 min
python scripts/06_prepare_network.py     # ~2-3 min
```

### 4. Launch Interactive Notebook
```bash
jupyter notebook notebooks/02_interactive_routing.ipynb
```

Edit the origin/destination in the notebook:
```python
origin_address = "Denver Union Station, Denver, CO"
dest_address = "Denver Art Museum, Denver, CO"
```

Run all cells → Get your safe route!

---

## 📊 What Each Component Does

### Data Pipeline Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `01_download_data.py` | Downloads Denver crime CSV (5 years) | `data/raw/crime_raw.csv` |
| `02_create_spatial_grid.py` | Creates 1,000ft × 1,000ft tiles over Denver | `spatial_grid.geojson`, `crime_filtered.csv` |
| `03_prepare_triplets.py` | Transforms to Cynet triplet format | `crime_triplets.pkl` |
| `04_train_model.py` | Trains Cynet model on 2019-2023 data | `cynet_model.pkl`, `model_metadata.json` |
| `05_validate_model.py` | Validates model on 2024+ data | `validation_results.json` |
| `06_prepare_network.py` | Downloads OSMnx network, creates tile-edge mapping | `denver_network.graphml`, `tile_edge_mapping.pkl` |

### Utility Modules

| Module | Key Functions |
|--------|---------------|
| `utils/spatial.py` | `create_spatial_grid()`, `validate_coordinates()`, `assign_points_to_tiles()` |
| `utils/cynet_wrapper.py` | `predict_next_4_hours()`, `prepare_cynet_data()` |
| `utils/routing.py` | `apply_risk_weights()`, `find_safe_route()`, `calculate_risk_reduction()` |

### Notebooks

| Notebook | Purpose |
|----------|---------|
| `00_data_exploration.ipynb` | Exploratory data analysis, crime patterns, heatmaps |
| `02_interactive_routing.ipynb` | **Main deliverable**: Generate safe routes with interactive maps |

---

## 🎯 How It Works

### The Algorithm

1. **Spatial Discretization**
   - Denver divided into 1,000ft × 1,000ft tiles (~500-1000 tiles)
   - Each crime incident assigned to a tile

2. **Temporal Binning**
   - Crime events aggregated into 1-hour bins
   - Binary matrix: 1 = crime occurred, 0 = no crime

3. **Cynet Training**
   - Learns spatio-temporal dependencies (Granger Network Inference)
   - Predicts 4-hour crime probability per tile

4. **Risk Weighting**
   - Each street edge gets risk from intersecting tiles
   - Formula: `edge_weight = edge_length × (1 + edge_risk)`

5. **Safe Routing**
   - Uses NetworkX to find path minimizing `risk_weight`
   - Compares to fastest route (minimizing `length`)

### The Risk Formula

For each edge in the street network:

```
edge_risk = Σ(P(crime_tile_i) × length_fraction_i)
edge_weight = edge_length × (1 + edge_risk)
```

Where:
- `P(crime_tile_i)` = Cynet prediction for tile i
- `length_fraction_i` = Proportion of edge in tile i

---

## 📈 Expected Results

After running the pipeline, you should have:

- **✅ ~500,000-1,000,000** crime records
- **✅ ~500-1,000** spatial tiles
- **✅ Binary spatiotemporal matrix** (tiles × hours)
- **✅ Trained model** with AUC > 0.55
- **✅ Street network** with ~50,000+ nodes
- **✅ Tile-edge mapping** for ~100,000+ edges

### Sample Output

```
ROUTE COMPARISON
======================================================================
route_name    length    cumulative_risk    travel_time    num_edges
safe          4523m     0.0234             342s           87
fastest       4102m     0.0456             289s           76

RISK REDUCTION ANALYSIS
======================================================================
Risk reduction: 48.7%
Absolute risk reduction: 0.0222
Length increase: 421m (10.3%)
```

---

## 🧪 Testing Guide

See **`TESTING.md`** for:
- Step-by-step verification tests
- Visual verification (heatmaps)
- Troubleshooting common issues
- Integration test scripts

Quick test:
```bash
python test_setup.py
```

---

## 🔧 Key Features

### ✅ Implemented

- Data download with caching
- Spatial tessellation (1,000ft tiles)
- Cynet triplet format transformation
- Model training with placeholder fallback
- OSMnx street network integration
- Tile-to-edge mapping (critical integration piece)
- Risk-weighted routing algorithm
- Interactive Folium maps
- Route comparison & metrics
- GeoJSON export

### 📝 Known Limitations

1. **Cynet dependency**: May not be on PyPI - placeholder model provided
2. **Cold start tiles**: Areas with no crime get zero risk
3. **Static network**: Doesn't account for traffic/closures
4. **Equal crime weighting**: All crimes treated equally
5. **Research prototype**: Not a safety guarantee

---

## 🎨 Customization Options

### Change Tile Size

Edit `scripts/02_create_spatial_grid.py`:
```python
TILE_SIZE_METERS = 305  # Change to 200, 500, etc.
```

### Change Prediction Window

Edit `scripts/04_train_model.py`:
```python
model = xgModels.xGenESeSS(
    lag_window=24,           # Change lookback
    prediction_horizon=4     # Change forecast window
)
```

### Change Risk Weighting Formula

Edit `scripts/utils/routing.py`:
```python
risk_weight = edge_length * (1 + edge_risk)  # Adjust multiplier
```

---

## 📚 Next Steps

### Option A: Test the MVP
1. Run `QUICKSTART.md` steps
2. Generate a route in the notebook
3. Verify outputs visually

### Option B: Install Cynet for Real Predictions
```bash
cd ~/
git clone https://github.com/zeroknowledgediscovery/Cynet
cd Cynet
pip install -e .
cd ~/guardian-route
python scripts/04_train_model.py  # Re-train with real Cynet
```

### Option C: Extend the System

Ideas for enhancements:
- Add crime severity weighting
- Integrate real-time crime feeds
- Build Flask/Streamlit web app
- Multi-city support
- Confidence intervals on predictions
- Time-of-day sensitivity

---

## 🐛 Troubleshooting

### "Cynet not found"
→ Expected! Placeholder model will work for testing.

### Download fails
→ Manual download:
```bash
curl -o data/raw/crime_raw.csv "https://www.denvergov.org/media/gis/DataCatalog/crime/csv/crime.csv"
```

### "No route found"
→ Check that origin/destination are within Denver bounds.

### Memory issues
→ Reduce data size or time resolution in scripts.

### OSMnx network download slow
→ May take 2-5 minutes for Denver. Be patient!

---

## 📖 Documentation Reference

- **README.md**: Project overview & background
- **QUICKSTART.md**: 5-minute getting started
- **TESTING.md**: Comprehensive testing guide
- **Implementation Plan**: `~/.claude/plans/memoized-crafting-sloth.md`

---

## 🎓 Research Citation

This project implements the methodology from:

> Rotaru et al. (2022). Event-level prediction of urban crime reveals a signature
> of enforcement bias in US cities. *Nature Human Behaviour*.
> https://doi.org/10.1038/s41562-022-01372-0

---

## ✅ Implementation Checklist

- [x] Project structure created
- [x] Requirements.txt with dependencies
- [x] Data download script
- [x] Spatial grid creation
- [x] Cynet triplet transformation
- [x] Model training (with fallback)
- [x] Model validation
- [x] OSMnx network download
- [x] Tile-edge mapping (critical!)
- [x] Risk weighting utilities
- [x] Safe routing algorithm
- [x] Interactive notebook (main deliverable)
- [x] Data exploration notebook
- [x] Testing documentation
- [x] README & quick start guide

**All components implemented! ✅**

---

## 🚀 You're Ready!

The Guardian Route MVP is complete. Follow **QUICKSTART.md** to get started!

Questions or issues? Check TESTING.md for troubleshooting.
