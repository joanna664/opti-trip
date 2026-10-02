# OptiTrip 🗺️
> An algorithmic day-trip itinerary optimizer built with Python and Streamlit.

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
## 3. Total Time Estimation
Total itinerary duration accounts for transit as well as site engagement:

$$T_{\text{total}} = T_{\text{walking}} + \sum_{k=1}^{N} T_{\text{visit}}(k)$$

$$T_{\text{walking}} = \frac{d_{\text{total}}}{v_{\text{walk}}} \times 60 \quad (\text{minutes})$$

Where $v_{\text{walk}} \approx 4.5 \text{ km/h}$ (average pedestrian walking speed) and $T_{\text{visit}}(k)$ is the user-allotted exploration duration at stop $k$.

---
## Demo & Screenshots