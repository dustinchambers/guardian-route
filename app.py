"""
Guardian Route - Streamlit Web App

Live safety-weighted routing for Denver.
Deploy to Streamlit Cloud for free public POC.
"""

import streamlit as st
import sys
from pathlib import Path
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import joblib
import pickle
import json
from datetime import datetime
import osmnx as ox

# Add scripts to path
sys.path.append(str(Path(__file__).parent / "scripts"))
from utils.routing import (
    apply_risk_weights,
    find_safe_route,
    calculate_route_metrics,
    calculate_risk_reduction,
    route_to_geodataframe,
    geocode_address
)
from utils.cynet_wrapper import predict_next_4_hours

# Page config
st.set_page_config(
    page_title="Guardian Route - Denver Safety Routing",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model():
    """Load trained model (cached)."""
    model = joblib.load('models/trained/cynet_model.pkl')
    with open('models/trained/model_metadata.json', 'r') as f:
        metadata = json.load(f)
    return model, metadata


@st.cache_resource
def load_network():
    """Load street network (cached)."""
    G = ox.load_graphml('data/network/denver_network.graphml')
    return G


@st.cache_resource
def load_tile_mapping():
    """Load tile-edge mapping (cached)."""
    with open('data/network/tile_edge_mapping.pkl', 'rb') as f:
        mapping = pickle.load(f)
    return mapping


@st.cache_resource
def load_tiles():
    """Load spatial grid (cached)."""
    tiles = gpd.read_file('data/processed/spatial_grid.geojson')
    return tiles


def create_map(origin_point, dest_point, safe_route_gdf, fast_route_gdf,
               tiles_with_risk, safe_metrics, fast_metrics):
    """Create Folium map with routes and risk heatmap."""

    center_lat = (origin_point[0] + dest_point[0]) / 2
    center_lon = (origin_point[1] + dest_point[1]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )

    # Risk heatmap
    folium.Choropleth(
        geo_data=tiles_with_risk,
        data=tiles_with_risk,
        columns=['tile_id', 'risk_prob'],
        key_on='feature.properties.tile_id',
        fill_color='YlOrRd',
        fill_opacity=0.4,
        line_opacity=0.1,
        legend_name='Crime Risk Probability',
        name='Risk Heatmap'
    ).add_to(m)

    # Safe route (green)
    if safe_route_gdf is not None:
        folium.GeoJson(
            safe_route_gdf,
            name='Safe Route',
            style_function=lambda x: {
                'color': 'green',
                'weight': 6,
                'opacity': 0.8
            },
            tooltip=f"Safe Route ({safe_metrics['length']:.0f}m)"
        ).add_to(m)

    # Fast route (blue dashed)
    if fast_route_gdf is not None:
        folium.GeoJson(
            fast_route_gdf,
            name='Fastest Route',
            style_function=lambda x: {
                'color': 'blue',
                'weight': 6,
                'opacity': 0.8,
                'dashArray': '10, 5'
            },
            tooltip=f"Fastest Route ({fast_metrics['length']:.0f}m)"
        ).add_to(m)

    # Markers
    folium.Marker(
        location=[origin_point[0], origin_point[1]],
        popup="<b>Origin</b>",
        icon=folium.Icon(color='green', icon='play')
    ).add_to(m)

    folium.Marker(
        location=[dest_point[0], dest_point[1]],
        popup="<b>Destination</b>",
        icon=folium.Icon(color='red', icon='stop')
    ).add_to(m)

    folium.LayerControl().add_to(m)

    return m


def main():
    """Main Streamlit app."""

    # Header
    st.markdown('<div class="main-header">🛡️ Guardian Route</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Safety-Weighted Routing for Denver</div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Origin input
        st.subheader("📍 Origin")
        origin_option = st.radio(
            "Input type:",
            ["Address", "Coordinates"],
            key="origin_type",
            horizontal=True
        )

        if origin_option == "Address":
            origin_address = st.text_input(
                "Starting address",
                value="Denver Union Station, Denver, CO",
                key="origin_addr"
            )
        else:
            col1, col2 = st.columns(2)
            with col1:
                origin_lat = st.number_input("Latitude", value=39.7539, format="%.4f", key="origin_lat")
            with col2:
                origin_lon = st.number_input("Longitude", value=-104.9979, format="%.4f", key="origin_lon")

        # Destination input
        st.subheader("🎯 Destination")
        dest_option = st.radio(
            "Input type:",
            ["Address", "Coordinates"],
            key="dest_type",
            horizontal=True
        )

        if dest_option == "Address":
            dest_address = st.text_input(
                "Destination address",
                value="Denver Art Museum, Denver, CO",
                key="dest_addr"
            )
        else:
            col1, col2 = st.columns(2)
            with col1:
                dest_lat = st.number_input("Latitude", value=39.7370, format="%.4f", key="dest_lat")
            with col2:
                dest_lon = st.number_input("Longitude", value=-104.9892, format="%.4f", key="dest_lon")

        # Time selection
        st.subheader("🕐 Departure Time")
        use_current_time = st.checkbox("Use current time", value=True)

        if not use_current_time:
            departure_date = st.date_input("Date", value=datetime.now())
            departure_hour = st.slider("Hour", 0, 23, datetime.now().hour)
            departure_time = datetime.combine(departure_date, datetime.min.time()).replace(hour=departure_hour)
        else:
            departure_time = datetime.now()

        st.caption(f"Predicting risk for: {departure_time.strftime('%Y-%m-%d %H:00')}")

        # Calculate button
        calculate_btn = st.button("🚀 Calculate Safe Route", type="primary", use_container_width=True)

    # Main content
    if calculate_btn:
        with st.spinner("Loading model and data..."):
            try:
                model, metadata = load_model()
                G = load_network()
                tile_edge_mapping = load_tile_mapping()
                tiles_gdf = load_tiles()

                st.success("✓ Model and network loaded")
            except Exception as e:
                st.error(f"Error loading data: {e}")
                st.info("Make sure you've run the data pipeline scripts first!")
                st.stop()

        # Geocode addresses
        with st.spinner("Geocoding addresses..."):
            try:
                if origin_option == "Address":
                    origin_point = geocode_address(origin_address)
                    if origin_point is None:
                        st.error(f"Could not geocode origin: {origin_address}")
                        st.stop()
                else:
                    origin_point = (origin_lat, origin_lon)

                if dest_option == "Address":
                    dest_point = geocode_address(dest_address)
                    if dest_point is None:
                        st.error(f"Could not geocode destination: {dest_address}")
                        st.stop()
                else:
                    dest_point = (dest_lat, dest_lon)

                st.success(f"✓ Origin: {origin_point}")
                st.success(f"✓ Destination: {dest_point}")
            except Exception as e:
                st.error(f"Geocoding error: {e}")
                st.stop()

        # Predict risk
        with st.spinner("Predicting crime risk..."):
            tile_risks = predict_next_4_hours(model, tiles_gdf, reference_time=departure_time)
            risk_df = pd.DataFrame(list(tile_risks.items()), columns=['tile_id', 'risk_prob'])
            tiles_with_risk = tiles_gdf.merge(risk_df, on='tile_id', how='left').fillna(0)

            avg_risk = sum(tile_risks.values()) / len(tile_risks)
            max_risk = max(tile_risks.values())
            st.success(f"✓ Risk predicted (avg: {avg_risk:.4f}, max: {max_risk:.4f})")

        # Calculate routes
        with st.spinner("Calculating routes..."):
            G_risk = apply_risk_weights(G.copy(), tile_edge_mapping, tile_risks)

            safe_route = find_safe_route(G_risk, origin_point, dest_point, weight='risk_weight')
            fast_route = find_safe_route(G_risk, origin_point, dest_point, weight='length')

            if safe_route is None or fast_route is None:
                st.error("Could not find routes. Check that origin/destination are in Denver.")
                st.stop()

            safe_route_gdf = route_to_geodataframe(G_risk, safe_route)
            fast_route_gdf = route_to_geodataframe(G_risk, fast_route)

            safe_metrics = calculate_route_metrics(G_risk, safe_route)
            fast_metrics = calculate_route_metrics(G_risk, fast_route)
            reduction = calculate_risk_reduction(safe_metrics, fast_metrics)

            st.success("✓ Routes calculated")

        # Display results
        st.header("📊 Route Comparison")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Risk Reduction",
                f"{reduction['risk_reduction_pct']:.1f}%",
                delta=f"{reduction['absolute_risk_reduction']:.4f}",
                delta_color="normal"
            )

        with col2:
            st.metric(
                "Safe Route Length",
                f"{safe_metrics['length']:.0f}m",
                delta=f"+{reduction['length_difference_m']:.0f}m" if reduction['length_difference_m'] > 0 else f"{reduction['length_difference_m']:.0f}m",
                delta_color="inverse"
            )

        with col3:
            st.metric(
                "Safe Route Risk",
                f"{reduction['safe_route_risk']:.4f}",
                delta=None
            )

        with col4:
            st.metric(
                "Fast Route Risk",
                f"{reduction['fast_route_risk']:.4f}",
                delta=None
            )

        # Trade-off summary
        st.info(
            f"💡 **Trade-off**: Travel {reduction['length_increase_pct']:.1f}% farther "
            f"for {reduction['risk_reduction_pct']:.1f}% less risk exposure"
        )

        # Map
        st.header("🗺️ Interactive Map")

        m = create_map(
            origin_point, dest_point,
            safe_route_gdf, fast_route_gdf,
            tiles_with_risk,
            safe_metrics, fast_metrics
        )

        st_folium(m, width=1200, height=600)

        # Legend
        st.markdown("""
        **Map Legend:**
        - 🟢 **Green solid line** = Safe route (minimizes risk)
        - 🔵 **Blue dashed line** = Fastest route (minimizes distance)
        - 🟥 **Red heatmap** = Crime risk intensity for next 4 hours
        """)

        # Detailed comparison
        with st.expander("📋 Detailed Route Comparison"):
            comparison_df = pd.DataFrame([
                {
                    'Route': 'Safe Route',
                    'Length (m)': f"{safe_metrics['length']:.0f}",
                    'Risk Score': f"{safe_metrics['cumulative_risk']:.4f}",
                    'Travel Time (s)': f"{safe_metrics['travel_time']:.0f}",
                    'Edges': safe_metrics['num_edges']
                },
                {
                    'Route': 'Fastest Route',
                    'Length (m)': f"{fast_metrics['length']:.0f}",
                    'Risk Score': f"{fast_metrics['cumulative_risk']:.4f}",
                    'Travel Time (s)': f"{fast_metrics['travel_time']:.0f}",
                    'Edges': fast_metrics['num_edges']
                }
            ])
            st.dataframe(comparison_df, use_container_width=True)

    else:
        # Welcome screen
        st.info("👈 Enter origin and destination in the sidebar, then click **Calculate Safe Route**")

        st.header("About Guardian Route")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🎯 What it does")
            st.markdown("""
            - Predicts crime risk across Denver using historical data
            - Generates routes that minimize exposure to high-risk areas
            - Compares safe routes vs. fastest routes
            - Accounts for time-of-day crime patterns
            """)

        with col2:
            st.subheader("⚙️ How it works")
            st.markdown("""
            - **Model**: Cynet algorithm (Granger Network Inference)
            - **Data**: 5 years of Denver crime incidents
            - **Resolution**: 1,000ft × 1,000ft tiles, 1-hour bins
            - **Routing**: OSMnx street network optimization
            """)

        st.warning("⚠️ **Disclaimer**: This is a research prototype for educational purposes. Route suggestions should not be considered safety guarantees.")


if __name__ == "__main__":
    main()
