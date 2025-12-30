#!/usr/bin/env python3
"""
Prepare Street Network and Tile-Edge Mapping

Downloads Denver street network via OSMnx and creates the critical
tile-to-edge mapping that bridges spatial predictions with routing.
"""

import os
import sys
from pathlib import Path
import pickle
import geopandas as gpd
import osmnx as ox
from shapely.geometry import LineString
from tqdm import tqdm

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_NETWORK_DIR = PROJECT_ROOT / "data" / "network"
GRID_PATH = DATA_PROCESSED_DIR / "spatial_grid.geojson"
NETWORK_PATH = DATA_NETWORK_DIR / "denver_network.graphml"
MAPPING_PATH = DATA_NETWORK_DIR / "tile_edge_mapping.pkl"


def download_street_network():
    """Download Denver street network via OSMnx."""
    print("\n" + "="*60)
    print("DOWNLOADING STREET NETWORK")
    print("="*60)

    # Check if network already exists
    if NETWORK_PATH.exists():
        print(f"Network file already exists: {NETWORK_PATH}")
        response = input("Re-download? (y/n): ").lower()
        if response != 'y':
            print("Using existing network file")
            return ox.load_graphml(NETWORK_PATH)

    print("Downloading Denver street network from OpenStreetMap...")
    print("This may take several minutes...")

    try:
        # Download network for drivable roads
        G = ox.graph_from_place(
            "Denver, Colorado, USA",
            network_type="drive"
        )

        print(f"\nDownloaded network:")
        print(f"  Nodes: {len(G.nodes):,}")
        print(f"  Edges: {len(G.edges):,}")

        # Add edge speeds and travel times
        print("\nAdding edge speeds and travel times...")
        G = ox.routing.add_edge_speeds(G)
        G = ox.routing.add_edge_travel_times(G)

        # Save network
        DATA_NETWORK_DIR.mkdir(parents=True, exist_ok=True)
        print(f"\nSaving network to: {NETWORK_PATH}")
        ox.save_graphml(G, NETWORK_PATH)

        file_size = NETWORK_PATH.stat().st_size / (1024 * 1024)
        print(f"Network file size: {file_size:.1f} MB")

        return G

    except Exception as e:
        print(f"\nError downloading network: {e}")
        print("\nTroubleshooting:")
        print("  1. Check internet connection")
        print("  2. Try smaller area: ox.graph_from_point((39.75, -104.87), dist=5000)")
        print("  3. Verify OSMnx installation: pip install --upgrade osmnx")
        sys.exit(1)


def create_tile_edge_mapping(G, tiles_gdf):
    """
    Create mapping of edges to tiles.

    For each edge, determines which tiles it intersects and the
    proportion of the edge length in each tile.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        Street network
    tiles_gdf : geopandas.GeoDataFrame
        Spatial grid

    Returns
    -------
    dict
        Mapping of edge_id to list of (tile_id, fraction) dicts
    """
    print("\n" + "="*60)
    print("CREATING TILE-EDGE MAPPING")
    print("="*60)

    # Convert network to GeoDataFrame
    print("Converting network to GeoDataFrame...")
    edges_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True)

    print(f"Network edges: {len(edges_gdf):,}")
    print(f"Spatial tiles: {len(tiles_gdf):,}")

    # Ensure both are in same CRS
    if edges_gdf.crs != tiles_gdf.crs:
        print(f"Converting CRS: {tiles_gdf.crs} -> {edges_gdf.crs}")
        tiles_gdf = tiles_gdf.to_crs(edges_gdf.crs)

    # Create spatial index for tiles (faster intersection lookups)
    print("\nBuilding spatial index...")
    tiles_sindex = tiles_gdf.sindex

    # Create mapping
    print("\nMapping edges to tiles...")
    edge_tile_mapping = {}
    edges_with_tiles = 0

    for edge_idx, edge_row in tqdm(edges_gdf.iterrows(), total=len(edges_gdf), desc="Processing edges"):
        edge_geom = edge_row['geometry']
        edge_length = edge_geom.length

        if edge_length == 0:
            continue

        # Find potentially intersecting tiles using spatial index
        possible_matches_idx = list(tiles_sindex.intersection(edge_geom.bounds))
        possible_matches = tiles_gdf.iloc[possible_matches_idx]

        # Check actual intersections
        tile_contributions = []

        for tile_idx, tile_row in possible_matches.iterrows():
            if edge_geom.intersects(tile_row['geometry']):
                # Calculate intersection length
                try:
                    intersection = edge_geom.intersection(tile_row['geometry'])

                    if intersection.is_empty:
                        continue

                    # Handle different geometry types
                    if hasattr(intersection, 'length'):
                        intersection_length = intersection.length
                    elif intersection.geom_type == 'Point':
                        intersection_length = 0
                    else:
                        intersection_length = 0

                    if intersection_length > 0:
                        fraction = intersection_length / edge_length
                        tile_contributions.append({
                            'tile_id': tile_row['tile_id'],
                            'fraction': fraction
                        })

                except Exception as e:
                    # Skip problematic intersections
                    continue

        if tile_contributions:
            # Normalize fractions to sum to 1.0
            total_fraction = sum(tc['fraction'] for tc in tile_contributions)
            if total_fraction > 0:
                for tc in tile_contributions:
                    tc['fraction'] = tc['fraction'] / total_fraction

            edge_tile_mapping[edge_idx] = tile_contributions
            edges_with_tiles += 1

    print(f"\nMapping complete:")
    print(f"  Edges mapped to tiles: {edges_with_tiles:,} / {len(edges_gdf):,}")
    print(f"  Coverage: {edges_with_tiles/len(edges_gdf)*100:.1f}%")

    return edge_tile_mapping


def save_mapping(edge_tile_mapping):
    """Save tile-edge mapping."""
    print("\n" + "="*60)
    print("SAVING MAPPING")
    print("="*60)

    print(f"Saving to: {MAPPING_PATH}")

    with open(MAPPING_PATH, 'wb') as f:
        pickle.dump(edge_tile_mapping, f, protocol=pickle.HIGHEST_PROTOCOL)

    file_size = MAPPING_PATH.stat().st_size / (1024 * 1024)
    print(f"Mapping file size: {file_size:.1f} MB")


def display_statistics(edge_tile_mapping):
    """Display mapping statistics."""
    print("\n" + "="*60)
    print("MAPPING STATISTICS")
    print("="*60)

    total_edges = len(edge_tile_mapping)
    tiles_per_edge = [len(tiles) for tiles in edge_tile_mapping.values()]

    if tiles_per_edge:
        print(f"Total mapped edges: {total_edges:,}")
        print(f"Average tiles per edge: {sum(tiles_per_edge)/len(tiles_per_edge):.2f}")
        print(f"Max tiles per edge: {max(tiles_per_edge)}")
        print(f"Edges with 1 tile: {sum(1 for t in tiles_per_edge if t == 1):,}")
        print(f"Edges with 2+ tiles: {sum(1 for t in tiles_per_edge if t > 1):,}")

        # Sample edge
        sample_edge_id = list(edge_tile_mapping.keys())[0]
        sample_tiles = edge_tile_mapping[sample_edge_id]
        print(f"\nSample edge mapping:")
        print(f"  Edge ID: {sample_edge_id}")
        for tile_info in sample_tiles[:3]:  # Show first 3 tiles
            print(f"    Tile: {tile_info['tile_id']}, Fraction: {tile_info['fraction']:.3f}")


def main():
    """Main execution."""
    print("="*60)
    print("STREET NETWORK PREPARATION")
    print("="*60)

    # Load spatial grid
    print("\nLoading spatial grid...")
    if not GRID_PATH.exists():
        print(f"Error: Spatial grid not found at {GRID_PATH}")
        print("Please run scripts/02_create_spatial_grid.py first")
        sys.exit(1)

    tiles_gdf = gpd.read_file(GRID_PATH)
    print(f"Loaded {len(tiles_gdf):,} tiles")

    # Download network
    G = download_street_network()

    # Create mapping
    edge_tile_mapping = create_tile_edge_mapping(G, tiles_gdf)

    # Save mapping
    save_mapping(edge_tile_mapping)

    # Display statistics
    display_statistics(edge_tile_mapping)

    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"\nOutputs:")
    print(f"  Network: {NETWORK_PATH}")
    print(f"  Tile-edge mapping: {MAPPING_PATH}")
    print("\nNext step: Open notebooks/02_interactive_routing.ipynb")


if __name__ == "__main__":
    main()
