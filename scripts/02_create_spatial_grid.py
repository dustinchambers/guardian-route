#!/usr/bin/env python3
"""
Create Spatial Grid and Filter Crime Data

Creates 1,000ft × 1,000ft spatial grid over Denver and filters crime data
for model training (2019-2023) and validation (2024-present).
"""

import os
import sys
from pathlib import Path
import pandas as pd
import geopandas as gpd
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from utils.spatial import (
    create_spatial_grid,
    validate_coordinates,
    assign_points_to_tiles,
    calculate_tile_statistics
)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CRIME_RAW_PATH = DATA_RAW_DIR / "crime_raw.csv"
CRIME_FILTERED_PATH = DATA_PROCESSED_DIR / "crime_filtered.csv"
GRID_PATH = DATA_PROCESSED_DIR / "spatial_grid.geojson"

# Data split dates
TRAIN_START = "2019-01-01"
TRAIN_END = "2024-01-01"

# Tile size in meters (305m ≈ 1,000 feet)
TILE_SIZE_METERS = 305


def load_and_filter_crime_data():
    """Load and filter crime data."""
    print("\n" + "="*60)
    print("LOADING CRIME DATA")
    print("="*60)

    if not CRIME_RAW_PATH.exists():
        print(f"Error: Crime data not found at {CRIME_RAW_PATH}")
        print("Please run scripts/01_download_data.py first")
        sys.exit(1)

    print(f"Reading: {CRIME_RAW_PATH}")
    df = pd.read_csv(CRIME_RAW_PATH)
    print(f"Loaded: {len(df):,} records")

    # Parse dates
    print("\nParsing dates...")
    df['FIRST_OCCURRENCE_DATE'] = pd.to_datetime(df['FIRST_OCCURRENCE_DATE'], errors='coerce')
    df = df[df['FIRST_OCCURRENCE_DATE'].notna()].copy()
    print(f"Records with valid dates: {len(df):,}")

    # Date range info
    min_date = df['FIRST_OCCURRENCE_DATE'].min()
    max_date = df['FIRST_OCCURRENCE_DATE'].max()
    print(f"Date range: {min_date.date()} to {max_date.date()}")

    # Filter coordinates
    print("\nValidating coordinates...")
    df = validate_coordinates(df, lon_col='GEO_LON', lat_col='GEO_LAT')

    # Add dataset split flag
    df['dataset'] = 'validation'  # Default to validation
    df.loc[df['FIRST_OCCURRENCE_DATE'] < TRAIN_END, 'dataset'] = 'training'

    train_count = (df['dataset'] == 'training').sum()
    val_count = (df['dataset'] == 'validation').sum()

    print(f"\nDataset split:")
    print(f"  Training ({TRAIN_START} to {TRAIN_END}): {train_count:,}")
    print(f"  Validation ({TRAIN_END} to present): {val_count:,}")

    return df


def create_and_save_grid():
    """Create spatial grid."""
    print("\n" + "="*60)
    print("CREATING SPATIAL GRID")
    print("="*60)

    grid = create_spatial_grid(tile_size_m=TILE_SIZE_METERS)

    # Save grid
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nSaving grid to: {GRID_PATH}")
    grid.to_file(GRID_PATH, driver='GeoJSON')

    return grid


def assign_tiles_and_save(df, grid):
    """Assign crime events to tiles and save."""
    print("\n" + "="*60)
    print("ASSIGNING EVENTS TO TILES")
    print("="*60)

    df_with_tiles = assign_points_to_tiles(df, grid, lon_col='GEO_LON', lat_col='GEO_LAT')

    # Remove events that didn't match a tile
    initial_count = len(df_with_tiles)
    df_with_tiles = df_with_tiles[df_with_tiles['tile_id'].notna()].copy()
    removed = initial_count - len(df_with_tiles)
    if removed > 0:
        print(f"Removed {removed:,} events outside grid")

    # Save filtered data
    print(f"\nSaving filtered data to: {CRIME_FILTERED_PATH}")
    df_with_tiles.to_csv(CRIME_FILTERED_PATH, index=False)

    return df_with_tiles


def display_summary(df, grid):
    """Display summary statistics."""
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)

    # Overall stats
    grid_with_stats = calculate_tile_statistics(df, grid)

    # Training set stats
    df_train = df[df['dataset'] == 'training']
    print(f"\nTraining dataset ({TRAIN_START} to {TRAIN_END}):")
    print(f"  Total events: {len(df_train):,}")
    print(f"  Unique tiles with events: {df_train['tile_id'].nunique():,}")
    print(f"  Date range: {df_train['FIRST_OCCURRENCE_DATE'].min().date()} to {df_train['FIRST_OCCURRENCE_DATE'].max().date()}")

    # Validation set stats
    df_val = df[df['dataset'] == 'validation']
    if len(df_val) > 0:
        print(f"\nValidation dataset ({TRAIN_END} to present):")
        print(f"  Total events: {len(df_val):,}")
        print(f"  Unique tiles with events: {df_val['tile_id'].nunique():,}")
        print(f"  Date range: {df_val['FIRST_OCCURRENCE_DATE'].min().date()} to {df_val['FIRST_OCCURRENCE_DATE'].max().date()}")

    # Top offense categories
    if 'OFFENSE_CATEGORY_ID' in df.columns:
        print(f"\nTop 5 offense categories:")
        top_offenses = df['OFFENSE_CATEGORY_ID'].value_counts().head(5)
        for offense, count in top_offenses.items():
            print(f"  {offense}: {count:,} ({count/len(df)*100:.1f}%)")

    # Temporal distribution
    df['hour'] = df['FIRST_OCCURRENCE_DATE'].dt.hour
    print(f"\nPeak crime hours:")
    top_hours = df['hour'].value_counts().head(5)
    for hour, count in top_hours.items():
        print(f"  {hour:02d}:00 - {hour:02d}:59: {count:,}")


def main():
    """Main execution."""
    print("="*60)
    print("SPATIAL GRID CREATION")
    print("="*60)

    # Load and filter data
    df = load_and_filter_crime_data()

    # Create grid
    grid = create_and_save_grid()

    # Assign tiles
    df_with_tiles = assign_tiles_and_save(df, grid)

    # Display summary
    display_summary(df_with_tiles, grid)

    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"\nOutputs:")
    print(f"  Grid: {GRID_PATH}")
    print(f"  Filtered data: {CRIME_FILTERED_PATH}")
    print("\nNext step: Run scripts/03_prepare_triplets.py")


if __name__ == "__main__":
    main()
