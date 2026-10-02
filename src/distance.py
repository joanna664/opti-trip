import math
from typing import List
from .models import Location


def haversine_distance(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
    """
    Calculates the great circle distance (in kilometers) between two points (lat, lon)
    using the Haversine formula.
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    # Radius of the Earth in kilometers
    R = 6371.0

    # Conversion of degrees to radians (radians)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c

    return round(distance, 3)


def create_distance_matrix(locations: List[Location]) -> list[list[float]]:
    """
    Creates an N x N distance matrix (in kilometers) between all locations.
    matrix[i][j] is the distance from location i to location j.
    """
    n = len(locations)
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = haversine_distance(
                    locations[i].to_coords(),
                    locations[j].to_coords()
                )
    return matrix