# OptiTrip 🗺️
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://optitrip.streamlit.app)

👉 **Live Demo:** [optitrip.streamlit.app](https://optitrip.streamlit.app)
> An algorithmic day-trip itinerary optimizer built with Python and Streamlit.  
> **Author:** Ioanna Georgiou

## Overview
OptiTrip solves a constrained Traveling Salesperson Problem (TSP) to calculate the shortest and most time-efficient route between points of interest in a city.

---
## Tech Stack
- **Language:** Python 3.11+
- **Frontend / Visualization:** Streamlit, Folium
- **Geocoding & Data:** Geopy (Nominatim), Pandas
---
## Setup & Installation
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
---
## Project Architecture
```text
optitrip/
│
├── src/
│   ├── __init__.py
│   ├── models.py          # Data classes (Location, RouteSolution)
│   ├── distance.py        # Haversine distance & N x N distance matrix builder
│   ├── optimizer.py       # TSP algorithms (Greedy Nearest Neighbor & 2-opt)
│   └── geocoding.py       # Address-to-coordinate resolution (Nominatim/OSM)
│
├── test_run.py            # Quick verification script for core logic
├── app.py                 # Streamlit web application & Folium map integration
├── requirements.txt       # Project dependencies
└── README.md              # Documentation & mathematical notes
```
---
## 1. Mathematical Formulation
### Distance Computation: Haversine Formula
Because urban points of interest exist on the Earth's curved surface, Euclidean distance is insufficient. OptiTrip computes the great-circle distance between two geographical points $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$ via the **Haversine formula**:

$$\Delta\sigma = 2 \arcsin \left( \sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)} \right)$$

$$d = R \cdot \Delta\sigma$$

Where:
* $R \approx 6371 \text{ km}$ (mean radius of the Earth)
* $\phi_1, \phi_2$: Geodesic latitude in radians
* $\lambda_1, \lambda_2$: Geodesic longitude in radians
* $d$: Spherical surface distance in kilometers

The computed pairwise distances populate an $N \times N$ symmetric distance matrix $D$, where $D_{ij}$ represents the traversal cost from location $i$ to location $j$.

---
## 2. Route Optimization Algorithm

Finding the global optimum for the TSP is **NP-hard** ($O((N-1)!/2)$ ). OptiTrip couples a fast constructive heuristic with a local search improvement:

1. **Greedy Nearest Neighbor (Construction Phase):**
   * Starts at the designated base node ($i=0$).
   * Iteratively transitions to the closest unvisited node:
     $$\text{next} = \arg\min_{j \in \text{Unvisited}} D_{\text{current}, j}$$
   * Time complexity: $\mathcal{O}(N^2)$.

2. **2-opt Local Search (Refinement Phase):**
   * Eliminates crossing path segments.
   * Systematically checks pairs of non-adjacent edges $(u, v)$ and $(x, y)$, reversing the intermediate sub-tour:
     $$\text{tour}_{\text{new}} = [t_0, \dots, t_{i-1}] + [t_k, t_{k-1}, \dots, t_i] + [t_{k+1}, \dots, t_n]$$
   * Replaces the tour whenever the new route length is strictly smaller ($\Delta D < 0$), iterating until a 2-optimal local minimum is achieved.

---
## 3.Realistic Street Routing (`src/routing.py`)
While Haversine distances guide fast combinatorial exploration, real urban travel follows topological road networks:
* **OSRM Foot Engine:** Connects to OpenStreetMap's Open Source Routing Machine (`/route/v1/foot`).
* **Turn-by-Turn Polyline:** Extracts actual pedestrian sidewalks, street turns, and plazas for map rendering instead of Euclidean straight lines.
* **Network Distance & Transit Time:** Computes true walking distances and transit durations based on street topology.

---

### 4. Dynamic Time Scheduling Model
OptiTrip translates spatial sequences into chronological clock-time itineraries:

$$T_{\text{arr}}(k) = T_{\text{dep}}(k-1) + \Delta t_{\text{walk}}(k-1 \to k)$$

$$T_{\text{dep}}(k) = T_{\text{arr}}(k) + T_{\text{visit}}(k)$$

Where $\Delta t_{\text{walk}}$ is resolved dynamically via OSRM street transit times.

---

## 🖥️ Interactive Web Application (`app.py`)

* **Geocoding & Safety Guardrails:**
  * Asynchronous coordinate resolution via OpenStreetMap.
  * **$50\text{ km}$ Urban Distance Barrier:** Automatically excludes out-of-city entries to prevent absurd multi-day walking calculations.
* **Interactive Folium Mapping:**
  * Displays turn-by-turn pedestrian street polyline on top of OpenStreetMap tiles.
  * Auto-centers map viewport with custom sequence pins and duration tooltips.
* **Chronological Schedule View:**
  * Clean UI containers showing specific arrival times, departure times, walking minutes, and site stays.
* **Google Maps Navigation Integration:**
  * Dynamically formats an encoded URL linking all stops as waypoints (`travelmode=walking`) for 1-click mobile GPS navigation.
* **Quick-Load City Presets:**
  * One-click presets for Athens, Rome, and Paris.