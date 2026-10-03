import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import urllib.parse

from src.models import Location
from src.geocoding import GeocodingService
from src.optimizer import solve_itinerary
from src.routing import OSRMRoutingService
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

# Services
@st.cache_resource
def get_geocoder():
    return GeocodingService()

geocoder = get_geocoder()

# --- SIDEBAR: INPUTS & PRESETS ---
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

    start_point = st.text_input("Start Point (e.g., Hotel)", key="start_point_val")

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
    <p>Algorithmic day-trip itinerary optimizer with realistic street network routing (OSRM + 2-opt).</p>
</div>
""", unsafe_allow_html=True)

# --- MAIN BODY ---
if run_button:
    with st.spinner("Fetching coordinates and solving TSP..."):
        locations = []
        loc_id = 0

        # 1. Geocode Start Point
        start_loc = geocoder.resolve_location(start_point, location_id=loc_id, duration_min=0)
        if not start_loc:
            st.error(f"Did not find coordinates for the start point: '{start_point}'")
            st.stop()
        locations.append(start_loc)
        loc_id += 1

        # 2. Parse & Validate POIs
        MAX_ALLOWED_DISTANCE_KM = 50.0

        for line in pois_text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(",")
            poi_name = parts[0].strip()
            duration = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 60

            loc = geocoder.resolve_location(poi_name, location_id=loc_id, duration_min=duration)
            if loc:
                dist_from_start = haversine_distance(start_loc.to_coords(), loc.to_coords())
                if dist_from_start > MAX_ALLOWED_DISTANCE_KM:
                    st.warning(
                        f"⚠ **Excluded point:** '{poi_name}' is {round(dist_from_start, 1)} km away. "
                        f"OptiTrip limit is {MAX_ALLOWED_DISTANCE_KM} km."
                    )
                else:
                    locations.append(loc)
                    loc_id += 1
            else:
                st.warning(f"⚠️ **Not found:** The point '{poi_name}' could not be resolved and was excluded.")

        if len(locations) < 2:
            st.warning("Please add at least one valid point of interest within 50 km of the starting location.")
            st.stop()

        # 3. Solve TSP
        solution = solve_itinerary(locations, start_idx=0, average_speed_kmh=walk_speed)

    # 4. Fetch Real Street Route via OSRM
    with st.spinner("Fetching pedestrian street network paths (OSRM)..."):
        stop_coords = [loc.to_coords() for loc in solution.ordered_locations]
        street_polyline, street_dist_km, street_walk_min = OSRMRoutingService.get_route_geometry(stop_coords)

        # Αν το OSRM επέστρεψε επιτυχώς πραγματική απόσταση, τη χρησιμοποιούμε
        effective_dist_km = street_dist_km if street_dist_km > 0 else solution.total_distance_km
        total_visits_min = sum(loc.visit_duration_min for loc in solution.ordered_locations)
        effective_walking_min = street_walk_min if street_walk_min > 0 else (effective_dist_km / walk_speed) * 60
        total_trip_min = round(effective_walking_min + total_visits_min, 1)

    # --- METRICS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("🚶‍♂️ Walking Distance (Streets)", f"{effective_dist_km} km")
    hours = int(total_trip_min // 60)
    minutes = int(total_trip_min % 60)
    col2.metric("⏱ Total Itinerary Time", f"{hours}h {minutes}m")
    col3.metric("📍 Total Stops", len(solution.ordered_locations))

    st.markdown("---")

    col_map, col_list = st.columns([7, 5])

    with col_map:
        st.subheader("🗺️ Street Network Route Map")
        
        center_lat = solution.ordered_locations[0].lat
        center_lon = solution.ordered_locations[0].lon
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="OpenStreetMap")

        # Σχεδιασμός πραγματικών μονοπατιών δρόμου (OSRM PolyLine)
        folium.PolyLine(
            street_polyline,
            color="#2563EB",
            weight=5,
            opacity=0.85
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
                    # Υπολογισμός πραγματικού σκέλους διαδρομής
                    leg_coords, leg_dist, leg_time = OSRMRoutingService.get_route_geometry([prev_loc.to_coords(), loc.to_coords()])
                    
                    if leg_dist == 0:
                        leg_dist = haversine_distance(prev_loc.to_coords(), loc.to_coords())
                        leg_time = (leg_dist / walk_speed) * 60
                    
                    arr_dt = current_dt + timedelta(minutes=leg_time)
                    dep_dt = arr_dt + timedelta(minutes=loc.visit_duration_min)
                    
                    arr_str = arr_dt.strftime("%H:%M")
                    dep_str = dep_dt.strftime("%H:%M")
                    
                    st.markdown(f"🔵 **Stop #{idx + 1}:** {loc.name}")
                    st.markdown(f"🕒 **Arrive:** `{arr_str}` &nbsp;|&nbsp; **Depart:** `{dep_str}`")
                    st.caption(f"🚶 Walking: ~{round(leg_time)} min ({leg_dist} km) &bull; Stay: {loc.visit_duration_min} min")
                    
                    current_dt = dep_dt

        # Google Maps URL
        origin_query = urllib.parse.quote(solution.ordered_locations[0].name)
        destination_query = urllib.parse.quote(solution.ordered_locations[-1].name)
        
        if len(solution.ordered_locations) > 2:
            waypoints = [loc.name for loc in solution.ordered_locations[1:-1]]
            waypoints_query = urllib.parse.quote("|".join(waypoints))
            gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_query}&destination={destination_query}&waypoints={waypoints_query}&travelmode=walking"
        else:
            gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_query}&destination={destination_query}&travelmode=walking"

        st.link_button("📱 Open Route in Google Maps", gmaps_url, use_container_width=True)
else:
    st.info("👈 Set points of interest in the sidebar and click **Calculate Optimal Route**.")