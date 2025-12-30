#!/usr/bin/env python3
"""
Prepare Cynet Triplet Format

Transforms crime data into Cynet's triplet format:
- row_coords: Spatial tiles (tile IDs)
- col_dates: Temporal bins (hourly timestamps)
- timeseries: Binary event occurrence matrix
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pickle
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CRIME_FILTERED_PATH = DATA_PROCESSED_DIR / "crime_filtered.csv"
TRIPLETS_PATH = DATA_PROCESSED_DIR / "crime_triplets.pkl"

# Data split dates
TRAIN_START = "2019-01-01"
TRAIN_END = "2024-01-01"


def load_filtered_data():
    """Load filtered crime data."""
    print("\n" + "="*60)
    print("LOADING FILTERED DATA")
    print("="*60)

    if not CRIME_FILTERED_PATH.exists():
        print(f"Error: Filtered data not found at {CRIME_FILTERED_PATH}")
        print("Please run scripts/02_create_spatial_grid.py first")
        sys.exit(1)

    print(f"Reading: {CRIME_FILTERED_PATH}")
    df = pd.read_csv(CRIME_FILTERED_PATH)
    df['FIRST_OCCURRENCE_DATE'] = pd.to_datetime(df['FIRST_OCCURRENCE_DATE'])
    print(f"Loaded: {len(df):,} records")

    return df


def create_hourly_bins(df, dataset='training'):
    """
    Create hourly time bins and count events per tile per hour.

    Parameters
    ----------
    df : pandas.DataFrame
        Crime data with tile_id and FIRST_OCCURRENCE_DATE
    dataset : str
        'training' or 'validation'

    Returns
    -------
    pandas.DataFrame
        Aggregated data with tile_id, hour_bin, event_count
    """
    print("\n" + "="*60)
    print(f"CREATING HOURLY BINS ({dataset.upper()})")
    print("="*60)

    # Filter to dataset
    df_subset = df[df['dataset'] == dataset].copy()
    print(f"Records in {dataset} set: {len(df_subset):,}")

    # Create hourly bins (floor to hour)
    df_subset['hour_bin'] = df_subset['FIRST_OCCURRENCE_DATE'].dt.floor('H')

    # Count events per tile per hour
    hourly_counts = df_subset.groupby(['tile_id', 'hour_bin']).size().reset_index(name='event_count')

    print(f"Unique tiles: {hourly_counts['tile_id'].nunique():,}")
    print(f"Time range: {hourly_counts['hour_bin'].min()} to {hourly_counts['hour_bin'].max()}")
    print(f"Total hourly tile observations: {len(hourly_counts):,}")

    return hourly_counts


def create_spatiotemporal_matrix(hourly_counts):
    """
    Create spatiotemporal matrix from hourly counts.

    Parameters
    ----------
    hourly_counts : pandas.DataFrame
        Hourly event counts per tile

    Returns
    -------
    pandas.DataFrame
        Pivot table with tiles as rows, hours as columns
    """
    print("\n" + "="*60)
    print("CREATING SPATIOTEMPORAL MATRIX")
    print("="*60)

    # Pivot: rows = tiles, columns = hours, values = event counts
    matrix = hourly_counts.pivot_table(
        index='tile_id',
        columns='hour_bin',
        values='event_count',
        fill_value=0
    )

    print(f"Matrix shape: {matrix.shape[0]:,} tiles × {matrix.shape[1]:,} hours")
    print(f"Sparsity: {(matrix == 0).sum().sum() / (matrix.shape[0] * matrix.shape[1]) * 100:.1f}% zeros")

    return matrix


def convert_to_binary(matrix, threshold=1):
    """
    Convert event counts to binary occurrence (0/1).

    Parameters
    ----------
    matrix : pandas.DataFrame
        Spatiotemporal matrix with event counts
    threshold : int
        Events threshold for binary classification

    Returns
    -------
    pandas.DataFrame
        Binary matrix (0 = no event, 1 = event occurred)
    """
    print("\n" + "="*60)
    print("CONVERTING TO BINARY")
    print("="*60)

    binary_matrix = (matrix >= threshold).astype(int)

    events_percent = (binary_matrix == 1).sum().sum() / (binary_matrix.shape[0] * binary_matrix.shape[1]) * 100
    print(f"Event occurrence rate: {events_percent:.2f}%")

    return binary_matrix


def create_triplet(binary_matrix):
    """
    Create Cynet triplet format.

    Parameters
    ----------
    binary_matrix : pandas.DataFrame
        Binary spatiotemporal matrix

    Returns
    -------
    dict
        Triplet with keys: row_coords, col_dates, timeseries
    """
    print("\n" + "="*60)
    print("CREATING TRIPLET FORMAT")
    print("="*60)

    triplet = {
        'row_coords': binary_matrix.index.values,  # Tile IDs
        'col_dates': binary_matrix.columns.values,  # Timestamps
        'timeseries': binary_matrix.values  # Binary matrix (numpy array)
    }

    print(f"Row coords (tiles): {len(triplet['row_coords']):,}")
    print(f"Column dates (hours): {len(triplet['col_dates']):,}")
    print(f"Timeseries shape: {triplet['timeseries'].shape}")
    print(f"Timeseries dtype: {triplet['timeseries'].dtype}")

    return triplet


def save_triplet(triplet, dataset='training'):
    """Save triplet to pickle file."""
    print("\n" + "="*60)
    print(f"SAVING TRIPLET ({dataset.upper()})")
    print("="*60)

    if dataset == 'training':
        output_path = TRIPLETS_PATH
    else:
        output_path = DATA_PROCESSED_DIR / f"crime_triplets_{dataset}.pkl"

    print(f"Saving to: {output_path}")

    with open(output_path, 'wb') as f:
        pickle.dump(triplet, f, protocol=pickle.HIGHEST_PROTOCOL)

    file_size = output_path.stat().st_size / (1024 * 1024)
    print(f"File size: {file_size:.1f} MB")

    return output_path


def display_sample(triplet):
    """Display sample of triplet data."""
    print("\n" + "="*60)
    print("TRIPLET SAMPLE")
    print("="*60)

    print(f"\nFirst 5 tiles:")
    for i, tile in enumerate(triplet['row_coords'][:5]):
        print(f"  {i}: {tile}")

    print(f"\nFirst 5 timestamps:")
    for i, ts in enumerate(triplet['col_dates'][:5]):
        print(f"  {i}: {ts}")

    print(f"\nTimeseries sample (first 5 tiles, first 10 hours):")
    sample = triplet['timeseries'][:5, :10]
    print(sample)

    print(f"\nTimeseries statistics:")
    total_cells = triplet['timeseries'].size
    total_events = triplet['timeseries'].sum()
    print(f"  Total cells: {total_cells:,}")
    print(f"  Total events (1s): {total_events:,}")
    print(f"  Event rate: {total_events/total_cells*100:.2f}%")


def main():
    """Main execution."""
    print("="*60)
    print("CYNET TRIPLET PREPARATION")
    print("="*60)

    # Load data
    df = load_filtered_data()

    # Process training data
    print("\n" + "="*60)
    print("PROCESSING TRAINING DATA")
    print("="*60)

    hourly_train = create_hourly_bins(df, dataset='training')
    matrix_train = create_spatiotemporal_matrix(hourly_train)
    binary_train = convert_to_binary(matrix_train)
    triplet_train = create_triplet(binary_train)
    display_sample(triplet_train)
    train_path = save_triplet(triplet_train, dataset='training')

    # Process validation data (if exists)
    if (df['dataset'] == 'validation').any():
        print("\n" + "="*60)
        print("PROCESSING VALIDATION DATA")
        print("="*60)

        hourly_val = create_hourly_bins(df, dataset='validation')
        matrix_val = create_spatiotemporal_matrix(hourly_val)
        binary_val = convert_to_binary(matrix_val)
        triplet_val = create_triplet(binary_val)
        val_path = save_triplet(triplet_val, dataset='validation')
    else:
        print("\n(No validation data available)")
        val_path = None

    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"\nOutputs:")
    print(f"  Training triplet: {train_path}")
    if val_path:
        print(f"  Validation triplet: {val_path}")
    print("\nNext step: Run scripts/04_train_model.py")


if __name__ == "__main__":
    main()
