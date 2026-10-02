from typing import Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from .models import Location


class GeocodingService:
    """Service for converting addresses/names to geographic coordinates."""

    def __init__(self, user_agent: str = "optitrip_student_project"):
        # The Nominatim geocoder requires a unique user agent name
        self.geolocator = Nominatim(user_agent=user_agent)

    def resolve_location(self, name: str, location_id: int = 1, duration_min: int = 60) -> Optional[Location]:
        """
        Searches for a location by text and returns a Location object.
        Returns None if the location is not found.
        """
        try:
            geo_result = self.geolocator.geocode(name, timeout=10)
            if geo_result:
                return Location(
                    id=location_id,
                    name=name,
                    lat=geo_result.latitude,
                    lon=geo_result.longitude,
                    visit_duration_min=duration_min
                )
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Error occurred while searching for the location '{name}': {e}")
            return None