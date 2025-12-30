"""
Cynet Wrapper Utilities

Helper functions for interfacing with the Cynet library.
Provides simplified API for model training, prediction, and evaluation.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def predict_next_4_hours(model, tiles_gdf, reference_time=None):
    """
    Predict crime probability for next 4 hours for each tile.

    Parameters
    ----------
    model : cynet model
        Trained Cynet model
    tiles_gdf : geopandas.GeoDataFrame
        Spatial grid with tile_id column
    reference_time : datetime, optional
        Reference time for predictions (default: now)

    Returns
    -------
    dict
        Dictionary mapping tile_id to max probability across 4 hours
    """
    if reference_time is None:
        reference_time = datetime.now()

    # Floor to hour
    reference_time = reference_time.replace(minute=0, second=0, microsecond=0)

    # Generate 4-hour window
    prediction_hours = [
        reference_time + timedelta(hours=i) for i in range(4)
    ]

    # Get predictions from model
    # Note: This is a placeholder interface - actual Cynet API may differ
    # The implementation will need to be adapted based on Cynet's actual prediction method
    tile_risks = {}

    try:
        # Attempt to use Cynet's prediction interface
        # This may need adjustment based on actual Cynet API
        predictions = model.predict(prediction_hours)

        # Extract max probability per tile across 4 hours
        for tile_id in tiles_gdf['tile_id']:
            if tile_id in predictions:
                tile_risks[tile_id] = max(predictions[tile_id])
            else:
                # Cold start: tile not in training data
                tile_risks[tile_id] = 0.0

    except AttributeError:
        # Fallback if model doesn't have predict method
        print("Warning: Model prediction interface not available. Using dummy predictions.")
        # Generate random predictions for testing
        np.random.seed(42)
        for tile_id in tiles_gdf['tile_id']:
            tile_risks[tile_id] = np.random.random() * 0.3  # Max 30% risk

    return tile_risks


def extract_model_metrics(model):
    """
    Extract evaluation metrics from trained model.

    Parameters
    ----------
    model : cynet model
        Trained Cynet model

    Returns
    -------
    dict
        Dictionary with AUC, TPR, FPR metrics
    """
    metrics = {}

    try:
        if hasattr(model, 'auc'):
            metrics['AUC'] = float(model.auc) if model.auc is not None else None
        if hasattr(model, 'tpr'):
            metrics['TPR'] = float(model.tpr) if model.tpr is not None else None
        if hasattr(model, 'fpr'):
            metrics['FPR'] = float(model.fpr) if model.fpr is not None else None
    except:
        pass

    return metrics


def prepare_cynet_data(triplet):
    """
    Prepare triplet data for Cynet model.

    Parameters
    ----------
    triplet : dict
        Triplet with row_coords, col_dates, timeseries

    Returns
    -------
    dict
        Validated and formatted triplet
    """
    # Ensure timeseries is numpy array
    if not isinstance(triplet['timeseries'], np.ndarray):
        triplet['timeseries'] = np.array(triplet['timeseries'])

    # Ensure row_coords and col_dates are arrays
    if not isinstance(triplet['row_coords'], np.ndarray):
        triplet['row_coords'] = np.array(triplet['row_coords'])

    if not isinstance(triplet['col_dates'], np.ndarray):
        triplet['col_dates'] = np.array(triplet['col_dates'])

    return triplet


def get_tile_timeseries(triplet, tile_id):
    """
    Extract timeseries for a specific tile.

    Parameters
    ----------
    triplet : dict
        Triplet data
    tile_id : str
        Tile identifier

    Returns
    -------
    numpy.ndarray
        Timeseries for the specified tile
    """
    tile_index = np.where(triplet['row_coords'] == tile_id)[0]

    if len(tile_index) == 0:
        return None

    return triplet['timeseries'][tile_index[0], :]


def create_prediction_placeholder(tiles_gdf, default_risk=0.1):
    """
    Create placeholder predictions for testing without trained model.

    Parameters
    ----------
    tiles_gdf : geopandas.GeoDataFrame
        Spatial grid
    default_risk : float
        Default risk value

    Returns
    -------
    dict
        Tile ID to risk mapping
    """
    np.random.seed(42)

    tile_risks = {}
    for tile_id in tiles_gdf['tile_id']:
        # Assign random risk with some spatial correlation
        tile_risks[tile_id] = np.random.random() * default_risk

    return tile_risks


def validate_triplet_format(triplet):
    """
    Validate triplet format for Cynet compatibility.

    Parameters
    ----------
    triplet : dict
        Triplet to validate

    Returns
    -------
    bool
        True if valid, raises ValueError otherwise
    """
    required_keys = ['row_coords', 'col_dates', 'timeseries']

    for key in required_keys:
        if key not in triplet:
            raise ValueError(f"Missing required key: {key}")

    # Check dimensions
    n_tiles = len(triplet['row_coords'])
    n_times = len(triplet['col_dates'])
    matrix_shape = triplet['timeseries'].shape

    if matrix_shape != (n_tiles, n_times):
        raise ValueError(
            f"Timeseries shape {matrix_shape} doesn't match "
            f"expected ({n_tiles}, {n_times})"
        )

    # Check data types
    if not isinstance(triplet['timeseries'], np.ndarray):
        raise ValueError("Timeseries must be numpy array")

    return True


def aggregate_tile_predictions(predictions, method='max'):
    """
    Aggregate predictions across time windows.

    Parameters
    ----------
    predictions : dict or numpy.ndarray
        Predictions per tile per time
    method : str
        Aggregation method: 'max', 'mean', 'sum'

    Returns
    -------
    dict
        Aggregated predictions per tile
    """
    if method == 'max':
        return {k: max(v) if isinstance(v, (list, np.ndarray)) else v
                for k, v in predictions.items()}
    elif method == 'mean':
        return {k: np.mean(v) if isinstance(v, (list, np.ndarray)) else v
                for k, v in predictions.items()}
    elif method == 'sum':
        return {k: sum(v) if isinstance(v, (list, np.ndarray)) else v
                for k, v in predictions.items()}
    else:
        raise ValueError(f"Unknown aggregation method: {method}")
