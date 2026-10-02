from typing import List, Tuple
from .models import Location, RouteSolution
from .distance import create_distance_matrix


def calculate_total_distance(tour: List[int], distance_matrix: List[List[float]]) -> float:
    """Calculates the total length (in km) of a route (tour)."""
    total = 0.0
    for i in range(len(tour) - 1):
        total += distance_matrix[tour[i]][tour[i + 1]]
    return round(total, 3)


def greedy_nearest_neighbor(distance_matrix: List[List[float]], start_idx: int = 0) -> List[int]:
    """
    Creates an initial solution by always selecting the nearest unvisited node.
    Returns the list with the indices of the points in the order of visit.
    """
    n = len(distance_matrix)
    unvisited = set(range(n))
    unvisited.remove(start_idx)
    
    tour = [start_idx]
    current = start_idx

    while unvisited:
        # Find the nearest unvisited node
        next_node = min(unvisited, key=lambda node: distance_matrix[current][node])
        tour.append(next_node)
        unvisited.remove(next_node)
        current = next_node

    return tour


def two_opt_swap(tour: List[int], i: int, k: int) -> List[int]:
    """
    Performs a 2-opt swap on the tour by reversing the segment from index i to k:
    tour[0 ... i-1] + tour[i ... k] (reversed) + tour[k+1 ... end]
    """
    new_tour = tour[:i] + tour[i:k + 1][::-1] + tour[k + 1:]
    return new_tour


def optimize_route_2opt(tour: List[int], distance_matrix: List[List[float]]) -> Tuple[List[int], float]:
    """
    Implements the 2-opt local search algorithm to eliminate crossing edges.
    The first point (starting point) remains fixed.
    """
    best_tour = tour[:]
    best_distance = calculate_total_distance(best_tour, distance_matrix)
    improved = True

    while improved:
        improved = False
        # Start from i = 1 so that we don't change the starting point (index 0)
        for i in range(1, len(best_tour) - 1):
            for k in range(i + 1, len(best_tour)):
                new_tour = two_opt_swap(best_tour, i, k)
                new_distance = calculate_total_distance(new_tour, distance_matrix)

                if new_distance < best_distance:
                    best_tour = new_tour
                    best_distance = new_distance
                    improved = True
                    break  # First-improvement strategy
            if improved:
                break

    return best_tour, best_distance


def solve_itinerary(locations: List[Location], start_idx: int = 0, average_speed_kmh: float = 4.5) -> RouteSolution:
    """
    Central function:
    1. Builds the distance matrix.
    2. Finds an initial route with Greedy.
    3. Optimizes with 2-opt.
    4. Calculates the estimated total time (walking + visits).
    """
    if len(locations) <= 1:
        return RouteSolution(
            ordered_locations=locations,
            total_distance_km=0.0,
            total_duration_min=float(locations[0].visit_duration_min if locations else 0.0)
        )

    # 1. Distance Matrix
    distance_matrix = create_distance_matrix(locations)

    # 2. Greedy Initial Tour
    greedy_tour = greedy_nearest_neighbor(distance_matrix, start_idx=start_idx)

    # 3. 2-opt Optimization
    optimized_indices, final_distance = optimize_route_2opt(greedy_tour, distance_matrix)

    # 4. Sort Location objects
    ordered_locations = [locations[idx] for idx in optimized_indices]

    # Calculate total time:
    # Walking time (in minutes) + Sum of visit durations at each point
    walking_time_hours = final_distance / average_speed_kmh
    walking_time_min = walking_time_hours * 60
    visits_time_min = sum(loc.visit_duration_min for loc in ordered_locations)
    total_duration_min = round(walking_time_min + visits_time_min, 1)

    return RouteSolution(
        ordered_locations=ordered_locations,
        total_distance_km=final_distance,
        total_duration_min=total_duration_min
    )