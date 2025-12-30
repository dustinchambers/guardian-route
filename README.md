# Guardian Route: Safety-Weighted Routing for Denver

A predictive urban analytics system that combines crime forecasting with intelligent routing to generate safer travel paths through Denver.

## Overview

Guardian Route uses the **Cynet** algorithm (Granger Network Inference) to predict crime risk across Denver in 1,000ft × 1,000ft spatial tiles, then integrates these predictions with street network routing via OSMnx to generate routes that minimize exposure to predicted high-risk areas.

### Key Features

- **Predictive Crime Modeling**: Forecasts 4-hour crime probability using spatio-temporal dependencies
- **Safety-Weighted Routing**: Generates routes that balance distance with predicted risk
- **Interactive Visualization**: Jupyter notebook with risk heatmaps and route comparisons
- **Data-Driven**: Uses 5+ years of Denver Open Data crime incidents

## Research Foundation

Based on the paper: [Event-level prediction of urban crime reveals a signature of enforcement bias in US cities](https://www.nature.com/articles/s41562-022-01372-0) (Chattopadhyay et al., Nature Human Behaviour 2022)

- **Methodology**: Granger Network Inference for spatio-temporal event prediction
- **Advantage**: Provides interpretable "Digital Twin" of city interactions for counterfactual analysis
- **Source Code**: [Cynet GitHub](https://github.com/zeroknowledgediscovery/Cynet)

## Installation

### Prerequisites

- Python 3.10 or 3.11
- macOS system dependencies:
  ```bash
  brew install python-tk spatialindex
  ```

### Setup

```bash
# Clone or download the project
cd guardian-route

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Usage

### 1. Data Pipeline

Download and preprocess Denver crime data:

```bash
# Download crime data from Denver Open Data
python scripts/01_download_data.py

# Create 1,000ft × 1,000ft spatial grid
python scripts/02_create_spatial_grid.py

# Transform to Cynet triplet format
python scripts/03_prepare_triplets.py
```

### 2. Model Training

Train the predictive model on historical data (2019-2023):

```bash
# Train Cynet model
python scripts/04_train_model.py

# Validate on 2024+ data
python scripts/05_validate_model.py
```

### 3. Network Preparation

Download and prepare the street network:

```bash
# Download OSMnx network and create tile-edge mapping
python scripts/06_prepare_network.py
```

### 4. Interactive Routing (Main Deliverable)

Launch Jupyter and open the interactive notebook:

```bash
jupyter notebook notebooks/02_interactive_routing.ipynb
```

The notebook provides:
- Origin/destination address input
- 4-hour crime risk predictions per tile
- Safe route vs. fastest route comparison
- Interactive map with risk heatmap visualization
- GeoJSON export of generated routes

## Project Structure

```
guardian-route/
├── data/
│   ├── raw/                  # Downloaded crime CSV
│   ├── processed/            # Filtered data, spatial grid, triplets
│   └── network/              # OSMnx network and tile-edge mapping
├── models/
│   └── trained/              # Cynet model and metadata
├── scripts/
│   ├── 01_download_data.py
│   ├── 02_create_spatial_grid.py
│   ├── 03_prepare_triplets.py
│   ├── 04_train_model.py
│   ├── 05_validate_model.py
│   ├── 06_prepare_network.py
│   └── utils/
│       ├── spatial.py        # Tile creation utilities
│       ├── cynet_wrapper.py  # Cynet interface helpers
│       └── routing.py        # Risk weight computation
├── notebooks/
│   ├── 00_data_exploration.ipynb
│   └── 02_interactive_routing.ipynb  # MAIN DELIVERABLE
└── outputs/
    └── routes/               # Generated GeoJSON routes
```

## Technical Details

### Risk Weighting Formula

For each street network edge:

```
edge_risk = Σ(P(Event_tile_i) × length_fraction_i)
edge_weight = edge_length × (1 + edge_risk)
```

Where:
- `P(Event_tile_i)` = Predicted crime probability in tile i
- `length_fraction_i` = Proportion of edge length in tile i

### Data Sources

- **Crime Data**: [Denver Open Data - Crime](https://www.denvergov.org/opendata)
  - URL: `https://www.denvergov.org/media/gis/DataCatalog/crime/csv/crime.csv`
  - Coverage: Previous 5 years + current year
  - Fields: GEO_LON, GEO_LAT, REPORTED_DATE, OFFENSE_CATEGORY_ID

- **Street Network**: OpenStreetMap via OSMnx
  - Downloaded for Denver, Colorado
  - Network type: Drivable roads

### Coordinate Systems

- **Input**: WGS84 (EPSG:4326) latitude/longitude
- **Tiling**: UTM Zone 13N (EPSG:32613) for accurate distance calculations
- **Output**: WGS84 (EPSG:4326) for compatibility

## Model Performance

Target metrics:
- AUC > 0.55 (better than random)
- Training data: 2019-2023 crime incidents
- Validation data: 2024-present
- Prediction window: Next 4 hours
- Spatial resolution: 1,000ft × 1,000ft tiles
- Temporal resolution: 1-hour bins

## Known Limitations

1. **Historical patterns only**: Does not account for special events (concerts, protests, sporting events)
2. **Cold start problem**: Tiles with zero historical crime receive zero risk
3. **Equal weighting**: All crime types weighted equally (no severity distinction)
4. **Static network**: Does not account for road closures, construction, or traffic conditions
5. **Research prototype**: Not a safety guarantee; for educational/research purposes only

## Future Enhancements

- Crime severity weighting (violent vs. property crimes)
- Multi-objective optimization (risk + distance + time)
- Prediction confidence intervals
- Real-time crime feed integration
- Multi-city support

## License

This project uses publicly available data from Denver Open Data Catalog (Creative Commons Attribution 3.0).

## Citation

If you use this work, please cite:

```
Rotaru et al. (2022). Event-level prediction of urban crime reveals a signature
of enforcement bias in US cities. Nature Human Behaviour.
https://doi.org/10.1038/s41562-022-01372-0
```

## Acknowledgments

- University of Chicago Zero Knowledge Discovery team for Cynet
- Denver Open Data Catalog
- OSMnx project by Geoff Boeing
