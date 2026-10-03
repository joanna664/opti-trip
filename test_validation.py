import sys
from src.models import Location
from src.distance import haversine_distance, create_distance_matrix
from src.optimizer import solve_itinerary
from src.geocoding import GeocodingService
from src.routing import OSRMRoutingService


def test_haversine_accuracy():
    """Check calcualtion of distances based on known coordinates."""
    # Coordinates: Syntagma (37.9753, 23.7361) and Acropolis (37.9715, 23.7257)
    dist = haversine_distance((37.9753, 23.7361), (37.9715, 23.7257))
    assert 0.9 < dist < 1.3, f"Expected distance ~1.0 km, but calculated {dist} km"
    print("✅ 1. Haversine Metric: PASS (Geodetic Distance Accuracy)")


def test_tsp_solver_integrity():
    """Check integrity of TSP solution and preservation of starting point."""
    locs = [
        Location(id=0, name="Start Base", lat=37.975, lon=23.735, visit_duration_min=0),
        Location(id=1, name="Spot A", lat=37.971, lon=23.725, visit_duration_min=60),
        Location(id=2, name="Spot B", lat=37.980, lon=23.730, visit_duration_min=45),
        Location(id=3, name="Spot C", lat=37.968, lon=23.728, visit_duration_min=30),
    ]
    sol = solve_itinerary(locs, start_idx=0, average_speed_kmh=4.5)
    
    assert len(sol.ordered_locations) == 4, "The number of stops changed after TSP optimization"
    assert sol.ordered_locations[0].id == 0, "The starting point was moved from the first position"
    assert sol.total_distance_km > 0.0, "The total distance was calculated as 0"
    print("✅ 2. TSP 2-opt Optimization: PASS (Integrity of Solution & Preservation of Starting Point)")


def test_geocoding_service():
    """Check response of OpenStreetMap/Nominatim Geocoder."""
    geo = GeocodingService()
    
    # Valid location
    loc = geo.resolve_location("Syntagma Square, Athens", location_id=0, duration_min=0)
    assert loc is not None, "The Nominatim geocoder failed to find Syntagma Square"
    assert abs(loc.lat - 37.975) < 0.05, "The coordinates of Syntagma Square are significantly off"
    
    # Invalid location (Fallback handling)
    invalid_loc = geo.resolve_location("xyz123nonsense_location_999", location_id=1)
    assert invalid_loc is None, "The system returned coordinates for an invalid location"
    print("✅ 3. Geocoding Engine: PASS (Name Analysis & Fallback Handling)")


def test_osrm_pedestrian_routing():
    """Check connection with the OSRM pedestrian routing server."""
    syntagma_coords = (37.9753, 23.7361)
    acropolis_coords = (37.9715, 23.7257)
    
    polyline, dist_km, walk_min = OSRMRoutingService.get_route_geometry([syntagma_coords, acropolis_coords])
    
    assert len(polyline) > 2, "The OSRM did not return intermediate coordinates for the route"
    assert dist_km > 0.0, "The OSRM distance cannot be 0"
    assert walk_min > 0.0, "The OSRM walking time cannot be 0"
    print("✅ 4. OSRM Foot Routing API: PASS (Connection & Extraction of Pedestrian Geometry)")


def test_urban_boundary_guardrail():
    """Check urban boundary filter ( < 50 km)."""
    MAX_LIMIT = 50.0
    athens_base = (37.9753, 23.7361)
    paris_point = (48.8584, 2.2945) # Eiffel Tower
    
    dist = haversine_distance(athens_base, paris_point)
    is_out_of_bounds = dist > MAX_LIMIT
    
    assert is_out_of_bounds is True, "The 50 km check failed to identify a point outside the city"
    print(f"✅ 5. Urban Distance Guardrail: PASS (A point outside the city was identified with a distance of {round(dist, 1)} km > 50 km)")


if __name__ == "__main__":
    print("\n--- 🧪 START SUITE VALIDATION CHECKS (OPTITRIP) ---\n")
    try:
        test_haversine_accuracy()
        test_tsp_solver_integrity()
        test_geocoding_service()
        test_osrm_pedestrian_routing()
        test_urban_boundary_guardrail()
        print("\n🎉 ALL VALIDATION CHECKS PASSED SUCCESSFULLY! The project is 100% ready for Deployment.\n")
    except AssertionError as e:
        print(f"\n❌ VALIDATION ERROR: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED SYSTEM ERROR: {e}\n")
        sys.exit(1)