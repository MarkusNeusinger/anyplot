""" pyplots.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_polygon,
    ggplot,
    labs,
    scale_alpha_identity,
    scale_color_gradient,
    scale_size_identity,
    theme,
    theme_minimal,
)


# Seed for reproducibility
np.random.seed(42)

# Major international airports with coordinates
airports = {
    "JFK": ("New York", 40.64, -73.78),
    "LAX": ("Los Angeles", 33.94, -118.41),
    "LHR": ("London", 51.47, -0.46),
    "CDG": ("Paris", 49.01, 2.55),
    "DXB": ("Dubai", 25.25, 55.36),
    "HND": ("Tokyo", 35.55, 139.78),
    "SIN": ("Singapore", 1.36, 103.99),
    "SYD": ("Sydney", -33.95, 151.18),
    "GRU": ("São Paulo", -23.43, -46.47),
    "JNB": ("Johannesburg", -26.14, 28.25),
    "FRA": ("Frankfurt", 50.03, 8.57),
    "HKG": ("Hong Kong", 22.31, 113.92),
    "PEK": ("Beijing", 40.08, 116.58),
    "ORD": ("Chicago", 41.97, -87.91),
    "MIA": ("Miami", 25.79, -80.29),
}

# Flight routes with passenger volume (thousands per year)
routes = [
    ("JFK", "LHR", 4200),
    ("JFK", "CDG", 2800),
    ("LAX", "HND", 3500),
    ("LAX", "SYD", 1800),
    ("LHR", "DXB", 3100),
    ("LHR", "SIN", 2600),
    ("LHR", "HKG", 2400),
    ("CDG", "JFK", 2900),
    ("DXB", "SIN", 2200),
    ("DXB", "LHR", 3000),
    ("HND", "SIN", 1900),
    ("SIN", "SYD", 2100),
    ("GRU", "MIA", 1500),
    ("GRU", "LHR", 1700),
    ("JNB", "LHR", 1400),
    ("JNB", "DXB", 1600),
    ("FRA", "JFK", 2300),
    ("FRA", "DXB", 1800),
    ("HKG", "LAX", 2000),
    ("HKG", "SIN", 2500),
    ("PEK", "LAX", 2200),
    ("PEK", "LHR", 1900),
    ("ORD", "LHR", 2100),
    ("ORD", "FRA", 1700),
    ("MIA", "GRU", 1400),
]


def great_circle_path(lon1, lat1, lon2, lat2, n_points=50):
    """Generate points along a great circle arc between two locations."""
    # Convert to radians
    lon1_r, lat1_r = np.radians(lon1), np.radians(lat1)
    lon2_r, lat2_r = np.radians(lon2), np.radians(lat2)

    # Angular distance
    d = np.arccos(np.sin(lat1_r) * np.sin(lat2_r) + np.cos(lat1_r) * np.cos(lat2_r) * np.cos(lon2_r - lon1_r))

    # Handle very short distances
    if d < 1e-10:
        return np.array([lon1, lon2]), np.array([lat1, lat2])

    # Interpolate along the great circle
    t = np.linspace(0, 1, n_points)
    a = np.sin((1 - t) * d) / np.sin(d)
    b = np.sin(t * d) / np.sin(d)

    x = a * np.cos(lat1_r) * np.cos(lon1_r) + b * np.cos(lat2_r) * np.cos(lon2_r)
    y = a * np.cos(lat1_r) * np.sin(lon1_r) + b * np.cos(lat2_r) * np.sin(lon2_r)
    z = a * np.sin(lat1_r) + b * np.sin(lat2_r)

    # Convert back to lat/lon
    lats = np.degrees(np.arctan2(z, np.sqrt(x**2 + y**2)))
    lons = np.degrees(np.arctan2(y, x))

    return lons, lats


# Build flight path dataframe
flight_paths = []
max_volume = max(r[2] for r in routes)

for i, (origin, dest, volume) in enumerate(routes):
    origin_name, origin_lat, origin_lon = airports[origin]
    dest_name, dest_lat, dest_lon = airports[dest]

    # Generate great circle path
    path_lons, path_lats = great_circle_path(origin_lon, origin_lat, dest_lon, dest_lat, n_points=40)

    # Normalize volume for styling
    norm_volume = volume / max_volume
    line_width = 0.5 + norm_volume * 2.0  # Range: 0.5 to 2.5
    alpha_val = 0.3 + norm_volume * 0.35  # Range: 0.3 to 0.65

    for j, (lon, lat) in enumerate(zip(path_lons, path_lats, strict=False)):
        flight_paths.append(
            {
                "route_id": i,
                "order": j,
                "lon": lon,
                "lat": lat,
                "volume": volume,
                "size": line_width,
                "alpha": alpha_val,
                "route": f"{origin_name} → {dest_name}",
            }
        )

df_flights = pd.DataFrame(flight_paths)

# Build airport points dataframe
airport_points = []
for code, (name, lat, lon) in airports.items():
    airport_points.append({"code": code, "name": name, "lat": lat, "lon": lon})
df_airports = pd.DataFrame(airport_points)

# Simplified continent outlines for basemap context
continents = []

# North America
na_lon = [
    -170,
    -168,
    -140,
    -125,
    -124,
    -117,
    -105,
    -97,
    -82,
    -77,
    -68,
    -55,
    -52,
    -80,
    -87,
    -97,
    -105,
    -125,
    -145,
    -165,
    -170,
]
na_lat = [60, 65, 70, 55, 48, 33, 25, 26, 25, 35, 45, 48, 45, 27, 30, 20, 22, 50, 60, 55, 60]
for i in range(len(na_lon)):
    continents.append({"continent": "N. America", "order": i, "lon": na_lon[i], "lat": na_lat[i]})

# South America
sa_lon = [-80, -68, -60, -50, -35, -40, -50, -55, -68, -72, -75, -80, -82, -80]
sa_lat = [10, 12, 5, 0, -5, -22, -35, -52, -55, -18, -5, 0, 8, 10]
for i in range(len(sa_lon)):
    continents.append({"continent": "S. America", "order": i, "lon": sa_lon[i], "lat": sa_lat[i]})

# Europe
eu_lon = [-10, 0, 10, 20, 30, 40, 50, 60, 50, 35, 25, 20, 10, 0, -10, -10]
eu_lat = [35, 37, 36, 35, 35, 40, 45, 55, 70, 70, 70, 65, 60, 50, 40, 35]
for i in range(len(eu_lon)):
    continents.append({"continent": "Europe", "order": i, "lon": eu_lon[i], "lat": eu_lat[i]})

# Africa
af_lon = [-17, -5, 10, 35, 50, 52, 43, 35, 30, 15, 0, -17, -17]
af_lat = [15, 37, 37, 32, 12, 0, -25, -35, -35, -25, 5, 20, 15]
for i in range(len(af_lon)):
    continents.append({"continent": "Africa", "order": i, "lon": af_lon[i], "lat": af_lat[i]})

# Asia
as_lon = [60, 80, 100, 120, 140, 145, 140, 130, 105, 100, 80, 60, 45, 30, 25, 30, 35, 50, 60]
as_lat = [55, 70, 75, 70, 55, 45, 35, 30, 0, 5, 10, 25, 30, 35, 42, 55, 70, 70, 55]
for i in range(len(as_lon)):
    continents.append({"continent": "Asia", "order": i, "lon": as_lon[i], "lat": as_lat[i]})

# Australia/Oceania
au_lon = [113, 125, 135, 145, 152, 150, 140, 130, 115, 113]
au_lat = [-22, -15, -12, -15, -25, -38, -38, -33, -35, -22]
for i in range(len(au_lon)):
    continents.append({"continent": "Australia", "order": i, "lon": au_lon[i], "lat": au_lat[i]})

df_continents = pd.DataFrame(continents)

# Create the connection lines map
plot = (
    ggplot()
    # Draw continent polygons as basemap
    + geom_polygon(
        aes(x="lon", y="lat", group="continent"),
        data=df_continents,
        fill="#E5E5E5",
        color="#AAAAAA",
        size=0.4,
        alpha=0.9,
    )
    # Draw flight routes as great circle arcs
    + geom_path(
        aes(x="lon", y="lat", group="route_id", color="volume", size="size", alpha="alpha"),
        data=df_flights,
        lineend="round",
    )
    # Draw airport markers at endpoints
    + geom_point(
        aes(x="lon", y="lat"),
        data=df_airports,
        color="#306998",
        fill="#FFD43B",
        size=5,
        shape="o",
        stroke=1.0,
        alpha=0.95,
    )
    # Scale settings
    + scale_size_identity()
    + scale_alpha_identity()
    + scale_color_gradient(low="#FFD43B", high="#C0392B", name="Passengers\n(thousands/year)")
    + coord_fixed(ratio=1.3, xlim=(-180, 180), ylim=(-60, 80))
    + labs(
        title="Global Flight Routes · map-connection-lines · plotnine · pyplots.ai", x="Longitude (°)", y="Latitude (°)"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=22, weight="bold"),
        axis_title=element_text(size=18),
        axis_text=element_text(size=14),
        legend_title=element_text(size=16),
        legend_text=element_text(size=12),
        legend_position="right",
        panel_grid_major=element_line(color="#DDDDDD", size=0.3, alpha=0.4),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#D4E8F7", alpha=0.6),
    )
)

# Save at 300 DPI for 4800x2700 px output
plot.save("plot.png", dpi=300, verbose=False)
