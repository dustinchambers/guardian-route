"""
Spatial Utilities for Guardian Route

Functions for creating spatial grids, coordinate transformations,
and spatial operations needed for tile-based analysis.
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import box, Point
import numpy as np


# Denver bounding box (approximate, in WGS84 lat/lon)
DENVER_BBOX = {
    'lat_min': 39.60,
    'lat_max': 39.90,
    'lon_min': -105.12,
    'lon_max': -104.60
}

# Coordinate Reference Systems
CRS_WGS84 = 'EPSG:4326'  # Lat/lon
CRS_UTM_13N = 'EPSG:32613'  # UTM Zone 13N for Denver


def create_spatial_grid(bbox=None, tile_size_m=305, crs_output=CRS_WGS84):
    """
    Create a spatial grid of square tiles.

    Parameters
    ----------
    bbox : dict, optional
        Bounding box with keys: lat_min, lat_max, lon_min, lon_max
        If None, uses default Denver bounding box
    tile_size_m : float, default=305
        Tile size in meters (305m = ~1,000ft)
    crs_output : str, default='EPSG:4326'
        Output coordinate reference system

    Returns
    -------
    geopandas.GeoDataFrame
        Grid with columns: tile_id, geometry, center_lon, center_lat
    """
    if bbox is None:
        bbox = DENVER_BBOX

    # Create corner points in WGS84
    sw_corner = Point(bbox['lon_min'], bbox['lat_min'])
    ne_corner = Point(bbox['lon_max'], bbox['lat_max'])

    # Convert to UTM for accurate distance-based tiling
    gdf_corners = gpd.GeoDataFrame(
        {'geometry': [sw_corner, ne_corner]},
        crs=CRS_WGS84
    )
    gdf_corners_utm = gdf_corners.to_crs(CRS_UTM_13N)

    # Get UTM bounds
    xmin = gdf_corners_utm.geometry.iloc[0].x
    ymin = gdf_corners_utm.geometry.iloc[0].y
    xmax = gdf_corners_utm.geometry.iloc[1].x
    ymax = gdf_corners_utm.geometry.iloc[1].y

    # Create grid in UTM
    x_coords = np.arange(xmin, xmax, tile_size_m)
    y_coords = np.arange(ymin, ymax, tile_size_m)

    tiles = []
    tile_ids = []

    for i, x in enumerate(x_coords):
        for j, y in enumerate(y_coords):
            tile_geom = box(x, y, x + tile_size_m, y + tile_size_m)
            tiles.append(tile_geom)
            tile_ids.append(f"tile_{i}_{j}")

    # Create GeoDataFrame in UTM
    grid_utm = gpd.GeoDataFrame(
        {'tile_id': tile_ids, 'geometry': tiles},
        crs=CRS_UTM_13N
    )

    # Convert to output CRS
    grid = grid_utm.to_crs(crs_output)

    # Add center coordinates
    centroids = grid.geometry.centroid
    grid['center_lon'] = centroids.x
    grid['center_lat'] = centroids.y

    print(f"Created spatial grid: {len(grid)} tiles")
    print(f"Tile size: {tile_size_m}m × {tile_size_m}m")
    print(f"Coverage: ({bbox['lon_min']:.4f}, {bbox['lat_min']:.4f}) to ({bbox['lon_max']:.4f}, {bbox['lat_max']:.4f})")

    return grid


def validate_coordinates(df, lon_col='GEO_LON', lat_col='GEO_LAT', bbox=None):
    """
    Validate and filter coordinates.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with coordinate columns
    lon_col : str
        Longitude column name
    lat_col : str
        Latitude column name
    bbox : dict, optional
        Bounding box for filtering

    Returns
    -------
    pandas.DataFrame
        Filtered DataFrame with valid coordinates
    """
    if bbox is None:
        bbox = DENVER_BBOX

    initial_count = len(df)

    # Remove zero coordinates
    df = df[(df[lon_col] != 0) & (df[lat_col] != 0)].copy()

    # Remove null coordinates
    df = df[df[lon_col].notna() & df[lat_col].notna()].copy()

    # Filter to bounding box
    df = df[
        (df[lat_col] >= bbox['lat_min']) &
        (df[lat_col] <= bbox['lat_max']) &
        (df[lon_col] >= bbox['lon_min']) &
        (df[lon_col] <= bbox['lon_max'])
    ].copy()

    removed = initial_count - len(df)
    print(f"Coordinate validation: {len(df):,} valid / {initial_count:,} total ({removed:,} removed)")

    return df


def assign_points_to_tiles(points_df, grid_gdf, lon_col='GEO_LON', lat_col='GEO_LAT'):
    """
    Assign point coordinates to spatial tiles.

    Parameters
    ----------
    points_df : pandas.DataFrame
        DataFrame with point coordinates
    grid_gdf : geopandas.GeoDataFrame
        Spatial grid with tile_id
    lon_col : str
        Longitude column name
    lat_col : str
        Latitude column name

    Returns
    -------
    pandas.DataFrame
        Original DataFrame with added 'tile_id' column
    """
    # Convert points to GeoDataFrame
    geometry = gpd.points_from_xy(points_df[lon_col], points_df[lat_col])
    points_gdf = gpd.GeoDataFrame(
        points_df,
        geometry=geometry,
        crs=CRS_WGS84
    )

    # Spatial join
    points_with_tiles = gpd.sjoin(
        points_gdf,
        grid_gdf[['tile_id', 'geometry']],
        how='left',
        predicate='within'
    )

    # Drop geometry column and return as DataFrame
    result = pd.DataFrame(points_with_tiles.drop(columns='geometry'))

    # Remove duplicate index column from spatial join
    if 'index_right' in result.columns:
        result = result.drop(columns='index_right')

    tiles_assigned = result['tile_id'].notna().sum()
    print(f"Assigned {tiles_assigned:,} / {len(result):,} points to tiles")

    return result


def get_denver_bounds():
    """
    Get Denver bounding box in WGS84 coordinates.

    Returns
    -------
    dict
        Bounding box with lat_min, lat_max, lon_min, lon_max
    """
    return DENVER_BBOX.copy()


def calculate_tile_statistics(df, grid_gdf):
    """
    Calculate statistics per tile.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with tile_id column
    grid_gdf : geopandas.GeoDataFrame
        Spatial grid

    Returns
    -------
    geopandas.GeoDataFrame
        Grid with added statistics columns
    """
    # Count events per tile
    tile_counts = df.groupby('tile_id').size().reset_index(name='event_count')

    # Merge with grid
    grid_with_stats = grid_gdf.merge(tile_counts, on='tile_id', how='left')
    grid_with_stats['event_count'] = grid_with_stats['event_count'].fillna(0).astype(int)

    print(f"Tile statistics:")
    print(f"  Tiles with events: {(grid_with_stats['event_count'] > 0).sum():,} / {len(grid_with_stats):,}")
    print(f"  Average events per tile: {grid_with_stats['event_count'].mean():.1f}")
    print(f"  Max events in tile: {grid_with_stats['event_count'].max():,}")

    return grid_with_stats


def convert_to_utm(gdf):
    """Convert GeoDataFrame to UTM Zone 13N."""
    return gdf.to_crs(CRS_UTM_13N)


def convert_to_wgs84(gdf):
    """Convert GeoDataFrame to WGS84 (lat/lon)."""
    return gdf.to_crs(CRS_WGS84)
