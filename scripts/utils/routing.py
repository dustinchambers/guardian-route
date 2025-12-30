"""
Routing Utilities for Guardian Route

Functions for applying risk weights to street network edges
and computing safe routes using OSMnx.
"""

import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import numpy as np


def apply_risk_weights(G, tile_edge_mapping, tile_risks):
    """
    Apply risk weights to network edges based on tile predictions.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        Street network graph
    tile_edge_mapping : dict
        Mapping of edge_id to list of (tile_id, fraction) tuples
    tile_risks : dict
        Mapping of tile_id to risk probability

    Returns
    -------
    networkx.MultiDiGraph
        Graph with 'risk_weight' attribute added to edges
    """
    print("Applying risk weights to edges...")

    edges_processed = 0
    edges_with_risk = 0

    for u, v, key, data in G.edges(keys=True, data=True):
        edge_id = (u, v, key)
        edge_length = data.get('length', 0)

        # Get tiles for this edge
        if edge_id in tile_edge_mapping:
            tile_contributions = tile_edge_mapping[edge_id]

            # Calculate weighted average risk
            edge_risk = 0.0
            for tile_info in tile_contributions:
                tile_id = tile_info['tile_id']
                fraction = tile_info['fraction']
                tile_risk = tile_risks.get(tile_id, 0.0)
                edge_risk += tile_risk * fraction

            edges_with_risk += 1
        else:
            # Edge not in any tile (outside coverage area)
            edge_risk = 0.0

        # Apply risk weighting formula: weight = length × (1 + risk)
        risk_weight = edge_length * (1 + edge_risk)

        # Add as edge attribute
        G[u][v][key]['risk'] = edge_risk
        G[u][v][key]['risk_weight'] = risk_weight

        edges_processed += 1

    print(f"Processed {edges_processed:,} edges")
    print(f"Edges with risk data: {edges_with_risk:,} ({edges_with_risk/edges_processed*100:.1f}%)")

    return G


def find_safe_route(G, origin_point, dest_point, weight='risk_weight'):
    """
    Find the safest route between two points.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        Street network with risk weights
    origin_point : tuple
        (latitude, longitude) of origin
    dest_point : tuple
        (latitude, longitude) of destination
    weight : str
        Edge attribute to minimize

    Returns
    -------
    list
        List of node IDs forming the route
    """
    # Find nearest nodes to origin and destination
    origin_node = ox.distance.nearest_nodes(G, origin_point[1], origin_point[0])
    dest_node = ox.distance.nearest_nodes(G, dest_point[1], dest_point[0])

    # Find shortest path by specified weight
    try:
        route = ox.routing.shortest_path(G, origin_node, dest_node, weight=weight)
        return route
    except nx.NetworkXNoPath:
        print(f"Warning: No path found between {origin_node} and {dest_node}")
        return None


def calculate_route_metrics(G, route):
    """
    Calculate metrics for a route.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        Street network
    route : list
        List of node IDs

    Returns
    -------
    dict
        Metrics including length, cumulative_risk, travel_time
    """
    if route is None or len(route) < 2:
        return {
            'length': 0,
            'cumulative_risk': 0,
            'travel_time': 0,
            'num_edges': 0
        }

    total_length = 0
    total_risk = 0
    total_time = 0
    num_edges = 0

    for i in range(len(route) - 1):
        u = route[i]
        v = route[i + 1]

        # Get edge data (handle MultiDiGraph - take first edge)
        edge_data = G.get_edge_data(u, v)
        if edge_data:
            # Get first edge key
            edge_key = list(edge_data.keys())[0]
            data = edge_data[edge_key]

            length = data.get('length', 0)
            risk = data.get('risk', 0)
            travel_time = data.get('travel_time', 0)

            total_length += length
            total_risk += risk * length  # Risk weighted by length
            total_time += travel_time
            num_edges += 1

    return {
        'length': total_length,
        'cumulative_risk': total_risk,
        'travel_time': total_time,
        'num_edges': num_edges
    }


def route_to_geodataframe(G, route):
    """
    Convert route to GeoDataFrame.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        Street network
    route : list
        List of node IDs

    Returns
    -------
    geopandas.GeoDataFrame
        Route as GeoDataFrame
    """
    if route is None:
        return None

    return ox.routing.route_to_gdf(G, route)


def compare_routes(G, routes_dict):
    """
    Compare multiple routes.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        Street network
    routes_dict : dict
        Dictionary of route_name: route pairs

    Returns
    -------
    pandas.DataFrame
        Comparison table
    """
    comparison = []

    for name, route in routes_dict.items():
        metrics = calculate_route_metrics(G, route)
        metrics['route_name'] = name
        comparison.append(metrics)

    df = pd.DataFrame(comparison)

    # Reorder columns
    cols = ['route_name', 'length', 'cumulative_risk', 'travel_time', 'num_edges']
    df = df[cols]

    return df


def load_network(network_path):
    """
    Load street network from GraphML file.

    Parameters
    ----------
    network_path : str or Path
        Path to GraphML file

    Returns
    -------
    networkx.MultiDiGraph
        Street network
    """
    print(f"Loading network from: {network_path}")
    G = ox.load_graphml(network_path)
    print(f"Loaded: {len(G.nodes):,} nodes, {len(G.edges):,} edges")
    return G


def geocode_address(address):
    """
    Geocode an address to (lat, lon).

    Parameters
    ----------
    address : str
        Address string

    Returns
    -------
    tuple
        (latitude, longitude)
    """
    try:
        lat, lon = ox.geocode(address)
        return (lat, lon)
    except Exception as e:
        print(f"Error geocoding '{address}': {e}")
        return None


def calculate_risk_reduction(safe_metrics, fast_metrics):
    """
    Calculate risk reduction percentage.

    Parameters
    ----------
    safe_metrics : dict
        Metrics for safe route
    fast_metrics : dict
        Metrics for fast route

    Returns
    -------
    dict
        Risk reduction statistics
    """
    safe_risk = safe_metrics['cumulative_risk']
    fast_risk = fast_metrics['cumulative_risk']

    if fast_risk == 0:
        risk_reduction_pct = 0
    else:
        risk_reduction_pct = ((fast_risk - safe_risk) / fast_risk) * 100

    length_difference = safe_metrics['length'] - fast_metrics['length']
    length_increase_pct = (length_difference / fast_metrics['length']) * 100 if fast_metrics['length'] > 0 else 0

    return {
        'risk_reduction_pct': risk_reduction_pct,
        'absolute_risk_reduction': fast_risk - safe_risk,
        'length_difference_m': length_difference,
        'length_increase_pct': length_increase_pct,
        'safe_route_risk': safe_risk,
        'fast_route_risk': fast_risk
    }


def export_route_geojson(route_gdf, output_path):
    """
    Export route to GeoJSON file.

    Parameters
    ----------
    route_gdf : geopandas.GeoDataFrame
        Route as GeoDataFrame
    output_path : str or Path
        Output file path

    Returns
    -------
    str
        Output path
    """
    route_gdf.to_file(output_path, driver='GeoJSON')
    print(f"Exported route to: {output_path}")
    return str(output_path)


def create_route_comparison_map(G, routes_dict, tile_risks=None, tiles_gdf=None):
    """
    Create interactive Folium map comparing routes.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        Street network
    routes_dict : dict
        Dictionary of route_name: route pairs
    tile_risks : dict, optional
        Tile risk predictions for heatmap
    tiles_gdf : geopandas.GeoDataFrame, optional
        Spatial grid for heatmap

    Returns
    -------
    folium.Map
        Interactive map
    """
    import folium

    # Get center point from first route
    first_route = list(routes_dict.values())[0]
    if first_route and len(first_route) > 0:
        center_node = first_route[0]
        center_point = (G.nodes[center_node]['y'], G.nodes[center_node]['x'])
    else:
        center_point = (39.75, -104.87)  # Denver center

    # Create map
    m = folium.Map(location=center_point, zoom_start=13)

    # Add risk heatmap if provided
    if tile_risks and tiles_gdf is not None:
        risk_df = pd.DataFrame(list(tile_risks.items()), columns=['tile_id', 'risk_prob'])
        tiles_with_risk = tiles_gdf.merge(risk_df, on='tile_id', how='left').fillna(0)

        folium.Choropleth(
            geo_data=tiles_with_risk,
            data=tiles_with_risk,
            columns=['tile_id', 'risk_prob'],
            key_on='feature.properties.tile_id',
            fill_color='YlOrRd',
            fill_opacity=0.4,
            line_opacity=0.1,
            legend_name='Crime Risk Probability'
        ).add_to(m)

    # Add routes
    colors = {'safe': 'green', 'fastest': 'blue', 'shortest': 'purple'}
    styles = {'safe': {'weight': 5, 'opacity': 0.8},
              'fastest': {'weight': 5, 'opacity': 0.8, 'dashArray': '5, 5'},
              'shortest': {'weight': 5, 'opacity': 0.8, 'dashArray': '10, 5'}}

    for name, route in routes_dict.items():
        if route:
            route_gdf = route_to_geodataframe(G, route)
            color = colors.get(name, 'gray')
            style = styles.get(name, {'weight': 5, 'opacity': 0.8})
            style['color'] = color

            folium.GeoJson(
                route_gdf,
                name=f'{name.capitalize()} Route',
                style_function=lambda x, s=style: s
            ).add_to(m)

    folium.LayerControl().add_to(m)

    return m
