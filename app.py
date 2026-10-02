import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

from src.models import Location
from src.geocoding import GeocodingService
from src.optimizer import solve_itinerary
from src.distance import haversine_distance

# --- Streamlit App Configuration ---
st.set_page_config(
    page_title="OptiTrip — Route Planner",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Banner CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .hero-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        padding: 22px 28px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
    }
    .hero-banner h1 {
        color: white !important;
        font-size: 2rem !important;
        margin-bottom: 6px;
    }
    .hero-banner p {
        color: #DBEAFE !important;
        font-size: 1rem;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Geocoding Service
@st.cache_resource
def get_geocoder():
    return GeocodingService()

geocoder = get_geocoder()

## --- SIDEBAR: INPUTS & PRESETS ---
# Αρχικοποίηση session state για τα πεδία
if "start_point_val" not in st.session_state:
    st.session_state.start_point_val = "Syntagma Square, Athens"
if "pois_text_val" not in st.session_state:
    st.session_state.pois_text_val = (
        "Acropolis of Athens, 120\n"
        "Acropolis Museum, 90\n"
        "National Garden Athens, 45\n"
        "Monastiraki, 60"
    )

def set_city_preset(start, pois):
    st.session_state.start_point_val = start
    st.session_state.pois_text_val = pois

with st.sidebar:
    st.header("📍 Settings & Points")
    
    st.markdown("**Quick Presets:**")
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        if st.button("Athens", use_container_width=True):
            set_city_preset(
                "Syntagma Square, Athens",
                "Acropolis of Athens, 120\nAcropolis Museum, 90\nNational Garden Athens, 45\nMonastiraki, 60"
            )
            st.rerun()

    with col_p2:
        if st.button("Rome", use_container_width=True):
            set_city_preset(
                "Roma Termini, Rome",
                "Colosseum, 120\nTrevi Fountain, 40\nPantheon Rome, 60\nPiazza Navona, 45"
            )
            st.rerun()

    with col_p3:
        if st.button("Paris", use_container_width=True):
            set_city_preset(
                "Gare du Nord, Paris",
                "Eiffel Tower, 120\nLouvre Museum, 150\nArc de Triomphe, 50\nNotre Dame, 60"
            )
            st.rerun()

    # Τα πεδία συνδέονται απευθείας με το session_state
    start_point = st.text_input(
        "Start Point (e.g., Hotel)",
        key="start_point_val"
    )

    pois_text = st.text_area(
        "Points of Interest & Stay (Name, Minutes):",
        key="pois_text_val",
        height=140
    )

    col_speed, col_time = st.columns(2)
    with col_speed:
        walk_speed = st.slider("Speed (km/h)", 3.0, 6.0, 4.5, 0.5)
    with col_time:
        start_time_input = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())

    run_button = st.button("🚀 Calculate Optimal Route", type="primary", use_container_width=True)

# --- HERO BANNER ---
st.markdown("""
<div class="hero-banner">
    <h1>OptiTrip 🗺️</h1>
    <p>Algorithmic day-trip itinerary optimizer powered by TSP heuristics (Greedy + 2-opt).</p>
</div>
""", unsafe_allow_html=True)

# --- MAIN BODY ---
if run_button:
    with st.spinner("Fetching coordinates and calculating optimal route..."):
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

    # --- METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("🚶‍♂️ Total Walking Distance", f"{solution.total_distance_km} km")
    hours = int(solution.total_duration_min // 60)
    minutes = int(solution.total_duration_min % 60)
    col2.metric("⏱ Total Itinerary Time", f"{hours}h {minutes}m")
    col3.metric("📍 Total Stops", len(solution.ordered_locations))

    st.markdown("---")

    col_map, col_list = st.columns([7, 5])

    with col_map:
        st.subheader("🗺️ Interactive Route Map")
        
        center_lat = solution.ordered_locations[0].lat
        center_lon = solution.ordered_locations[0].lon
        
        # 100% ανοιχτός χάρτης χωρίς API keys
        m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="OpenStreetMap")

        # Διαδρομή
        route_coords = [loc.to_coords() for loc in solution.ordered_locations]
        folium.PolyLine(
            route_coords,
            color="#2563EB",
            weight=4,
            opacity=0.85,
            dash_array="6"
        ).add_to(m)

        # Pins
        for idx, loc in enumerate(solution.ordered_locations):
            is_start = (idx == 0)
            icon_color = "green" if is_start else "blue"
            icon_name = "play" if is_start else "info-sign"
            popup_text = f"<b>#{idx + 1} {loc.name}</b><br>Stay: {loc.visit_duration_min} min"
            
            folium.Marker(
                location=loc.to_coords(),
                popup=popup_text,
                tooltip=f"#{idx + 1}: {loc.name}",
                icon=folium.Icon(color=icon_color, icon=icon_name)
            ).add_to(m)

        st_folium(m, width="100%", height=530, returned_objects=[])

    with col_list:
        st.subheader("📋 Timetable & Schedule")
        
        current_dt = datetime.combine(datetime.today(), start_time_input)
        
        for idx, loc in enumerate(solution.ordered_locations):
            is_start = (idx == 0)
            
            with st.container(border=True):
                if is_start:
                    dep_time = current_dt.strftime("%H:%M")
                    st.markdown(f"🟢 **Start Point:** {loc.name}")
                    st.caption(f"🚩 Departure: **{dep_time}**")
                else:
                    prev_loc = solution.ordered_locations[idx - 1]
                    leg_distance = haversine_distance(prev_loc.to_coords(), loc.to_coords())
                    transit_min = (leg_distance / walk_speed) * 60
                    
                    arr_dt = current_dt + timedelta(minutes=transit_min)
                    dep_dt = arr_dt + timedelta(minutes=loc.visit_duration_min)
                    
                    arr_str = arr_dt.strftime("%H:%M")
                    dep_str = dep_dt.strftime("%H:%M")
                    
                    st.markdown(f"🔵 **Stop #{idx + 1}:** {loc.name}")
                    st.markdown(f"🕒 **Arrive:** `{arr_str}` &nbsp;|&nbsp; **Depart:** `{dep_str}`")
                    st.caption(f"🚶 Transit: ~{round(transit_min)} min ({round(leg_distance, 2)} km) &bull; Stay: {loc.visit_duration_min} min")
                    
                    current_dt = dep_dt
else:
    st.info("👈 Set points of interest in the sidebar and click **Calculate Optimal Route**.")