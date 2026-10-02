import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

from src.models import Location
from src.geocoding import GeocodingService
from src.optimizer import solve_itinerary

# --- Streamlit App Configuration ---
st.set_page_config(
    page_title="OptiTrip - Route Planner",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ OptiTrip: Smart Itinerary Optimizer")
st.caption("Calculate the best route for a day trip using the TSP algorithm (Greedy + 2-opt)")

# Initialize Geocoding Service
@st.cache_resource
def get_geocoder():
    return GeocodingService()

geocoder = get_geocoder()

# --- SIDEBAR: INPUTS ---
st.sidebar.header("📍 Settings & Points")

start_point = st.sidebar.text_input(
    "Start Point (e.g., Hotel)",
    value="Syntagma Square, Athens"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Points of Interest (POIs)")

# Προκαθορισμένα examples για ευκολία
default_pois = (
    "Acropolis of Athens, 120\n"
    "Acropolis Museum, 90\n"
    "National Garden Athens, 45\n"
    "Monastiraki, 60"
)

pois_text = st.sidebar.text_area(
    "Enter points and visit durations (Name, Minutes):",
    value=default_pois,
    height=150
)

walk_speed = st.sidebar.slider(
    "Walking Speed (km/h)",
    min_value=3.0,
    max_value=6.0,
    value=4.5,
    step=0.5
)

run_button = st.sidebar.button("🚀 Calculate Optimal Route", type="primary")

# --- MAIN BODY ---
if run_button:
    with st.spinner("Fetching coordinates and calculating route..."):
        locations = []
        loc_id = 0

        # 1. Geocode Start Point
        start_loc = geocoder.resolve_location(start_point, location_id=loc_id, duration_min=0)
        if not start_loc:
            st.error(f"Did not find coordinates for the start point: '{start_point}'")
            st.stop()
        
        locations.append(start_loc)
        loc_id += 1

        # 2. Parse & Geocode POIs
        for line in pois_text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(",")
            poi_name = parts[0].strip()
            duration = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 60

            loc = geocoder.resolve_location(poi_name, location_id=loc_id, duration_min=duration)
            if loc:
                locations.append(loc)
                loc_id += 1
            else:
                st.warning(f"Warning: The point '{poi_name}' was not recognized and has been excluded.")

        if len(locations) < 2:
            st.warning("Please add at least one valid point of interest.")
            st.stop()

        # 3. Solve TSP
        solution = solve_itinerary(locations, start_idx=0, average_speed_kmh=walk_speed)

    # --- DISPLAY RESULTS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("🚶‍♂️ Total Distance", f"{solution.total_distance_km} km")
    hours = int(solution.total_duration_min // 60)
    minutes = int(solution.total_duration_min % 60)
    col2.metric("⏱️️ Total Time", f"{hours}h {minutes}m")
    col3.metric("📍 Total Stops", len(solution.ordered_locations))

    col_map, col_list = st.columns([3, 2])

    with col_map:
        st.subheader("🗺️ Interactive Map")
        
        # Center the map on the start point
        center_lat = solution.ordered_locations[0].lat
        center_lon = solution.ordered_locations[0].lon
        # ΝΕΟ (100% ανοιχτό, χωρίς κανένα κλειδί ή υδατογράφημα):
        m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="OpenStreetMap")

        # Draw the route line
        route_coords = [loc.to_coords() for loc in solution.ordered_locations]
        folium.PolyLine(
            route_coords,
            color="#2563EB",
            weight=4,
            opacity=0.8,
            dash_array="6"
        ).add_to(m)

        # Add Markers with sequence numbers
        for idx, loc in enumerate(solution.ordered_locations):
            icon_color = "green" if idx == 0 else "blue"
            popup_text = f"<b>#{idx + 1} {loc.name}</b><br>Stay: {loc.visit_duration_min} min"
            
            folium.Marker(
                location=loc.to_coords(),
                popup=popup_text,
                tooltip=f"{idx + 1}. {loc.name}",
                icon=folium.Icon(color=icon_color, icon="info-sign")
            ).add_to(m)

        # Display the map in Streamlit
        st_folium(m, width="100%", height=500, returned_objects=[])

    with col_list:
        st.subheader("📋 Itinerary")
        itinerary_data = []
        for idx, loc in enumerate(solution.ordered_locations, start=1):
            role = "Start" if idx == 1 else f"Stop {idx}"
            itinerary_data.append({
                "Order": idx,
                "Point": loc.name,
                "Duration (min)": loc.visit_duration_min
            })
        
        df = pd.DataFrame(itinerary_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.info("💡 The itinerary was automatically optimized using the 2-opt algorithm to minimize unnecessary travel.")
else:
    st.info("👈 Set the points of interest in the left column and click **Compute Optimal Itinerary**.")