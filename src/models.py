from dataclasses import dataclass
from typing import Optional


@dataclass
class Location:
    """Represent a point of interest (POI) or a starting point."""
    id: int
    name: str
    lat: float
    lon: float
    visit_duration_min: int = 60  # Average visit duration in minutes
    opening_time: Optional[str] = None  # e.g., "09:00"
    closing_time: Optional[str] = None  # e.g., "17:00"

    def to_coords(self) -> tuple[float, float]:
        """Returns the coordinate pair (latitude, longitude)."""
        return (self.lat, self.lon)


@dataclass
class RouteSolution:
    """Represents the result of the optimization algorithm."""
    ordered_locations: list[Location]
    total_distance_km: float
    total_duration_min: float