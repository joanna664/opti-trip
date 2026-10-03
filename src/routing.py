import requests
from typing import List, Tuple, Dict, Any


class OSRMRoutingService:
    """ Extraction of real walking paths through OSRM API."""

    BASE_URL = "https://router.project-osrm.org/route/v1/foot"

    @classmethod
    def get_route_geometry(cls, coordinates: List[Tuple[float, float]]) -> Tuple[List[Tuple[float, float]], float, float]:
        """
        Accepts a list of coordinates [(lat, lon), ...] in the order of visit.
        Returns:
        - polyline_coords: List of coordinates for plotting on Folium [(lat, lon), ...]
        - total_distance_km: Real route distance in kilometers
        - total_duration_min: Real walking duration in minutes
        """
        if len(coordinates) < 2:
            return coordinates, 0.0, 0.0

        # The OSRM requires format: lon,lat;lon,lat;...
        coords_str = ";".join([f"{lon:.6f},{lat:.6f}" for lat, lon in coordinates])
        url = f"{cls.BASE_URL}/{coords_str}?overview=full&geometries=geojson"

        try:
            response = requests.get(url, timeout=10)
            data: Dict[str, Any] = response.json()

            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                total_distance_km = round(route["distance"] / 1000.0, 2)
                total_duration_min = round(route["duration"] / 60.0, 1)

                # The GeoJSON gives [lon, lat], Folium needs [lat, lon]
                raw_coords = route["geometry"]["coordinates"]
                polyline_coords = [(pt[1], pt[0]) for pt in raw_coords]

                return polyline_coords, total_distance_km, total_duration_min
        except Exception as e:
            print(f"Error occurred while calling OSRM: {e}")

        # Fallback: If the OSRM API fails, return the straight-line coordinates
        return coordinates, 0.0, 0.0