"""anyplot.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: plotnine | Python 3.13
Quality: pending | Updated: 2026-05-28
"""

import os
import sys


# Prevent self-import (this file shares its name with the plotnine library)
_here = os.path.abspath(os.path.dirname(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _here]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_polygon,
    ggplot,
    labs,
    scale_color_gradient,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # anyplot palette position 1
LAND_FILL = "#E0DED4" if THEME == "light" else "#282824"
LAND_BORDER = "#BCBBB1" if THEME == "light" else "#3A3A30"

TITLE = "Global Flight Routes · map-connection-lines · python · plotnine · anyplot.ai"
_n = len(TITLE)
TITLE_SIZE = max(8, round(12 * 67 / _n)) if _n > 67 else 12

np.random.seed(42)

# Major international airports: code → (city, lat, lon)
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

# Flight routes: (origin, destination, annual passengers in thousands)
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

# Build flight path dataframe — great circle arcs computed inline
flight_paths = []
N_PTS = 50

for route_i, (origin, dest, volume) in enumerate(routes):
    _, olat, olon = airports[origin]
    _, dlat, dlon = airports[dest]

    lon1_r, lat1_r = np.radians(olon), np.radians(olat)
    lon2_r, lat2_r = np.radians(dlon), np.radians(dlat)
    d = np.arccos(
        np.clip(np.sin(lat1_r) * np.sin(lat2_r) + np.cos(lat1_r) * np.cos(lat2_r) * np.cos(lon2_r - lon1_r), -1.0, 1.0)
    )
    if d < 1e-10:
        arc_lons = np.array([olon, dlon])
        arc_lats = np.array([olat, dlat])
    else:
        t = np.linspace(0, 1, N_PTS)
        a_c = np.sin((1 - t) * d) / np.sin(d)
        b_c = np.sin(t * d) / np.sin(d)
        x = a_c * np.cos(lat1_r) * np.cos(lon1_r) + b_c * np.cos(lat2_r) * np.cos(lon2_r)
        y = a_c * np.cos(lat1_r) * np.sin(lon1_r) + b_c * np.cos(lat2_r) * np.sin(lon2_r)
        z = a_c * np.sin(lat1_r) + b_c * np.sin(lat2_r)
        arc_lats = np.degrees(np.arctan2(z, np.sqrt(x**2 + y**2)))
        arc_lons = np.degrees(np.arctan2(y, x))

    for step, (lon, lat) in enumerate(zip(arc_lons, arc_lats, strict=True)):
        flight_paths.append({"route_id": route_i, "step": step, "lon": lon, "lat": lat, "volume": volume})

df_flights = pd.DataFrame(flight_paths)

# Airport endpoint markers
df_airports = pd.DataFrame([{"code": code, "lat": lat, "lon": lon} for code, (_, lat, lon) in airports.items()])

# Simplified continent polygons for basemap context
continents = []

for i, (lo, la) in enumerate(
    zip(
        [
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
        ],
        [60, 65, 70, 55, 48, 33, 25, 26, 25, 35, 45, 48, 45, 27, 30, 20, 22, 50, 60, 55, 60],
        strict=True,
    )
):
    continents.append({"continent": "N. America", "order": i, "lon": lo, "lat": la})

for i, (lo, la) in enumerate(
    zip(
        [-80, -68, -60, -50, -35, -40, -50, -55, -68, -72, -75, -80, -82, -80],
        [10, 12, 5, 0, -5, -22, -35, -52, -55, -18, -5, 0, 8, 10],
        strict=True,
    )
):
    continents.append({"continent": "S. America", "order": i, "lon": lo, "lat": la})

for i, (lo, la) in enumerate(
    zip(
        [-10, 0, 10, 20, 30, 40, 50, 60, 50, 35, 25, 20, 10, 0, -10, -10],
        [35, 37, 36, 35, 35, 40, 45, 55, 70, 70, 70, 65, 60, 50, 40, 35],
        strict=True,
    )
):
    continents.append({"continent": "Europe", "order": i, "lon": lo, "lat": la})

for i, (lo, la) in enumerate(
    zip(
        [-17, -5, 10, 35, 50, 52, 43, 35, 30, 15, 0, -17, -17],
        [15, 37, 37, 32, 12, 0, -25, -35, -35, -25, 5, 20, 15],
        strict=True,
    )
):
    continents.append({"continent": "Africa", "order": i, "lon": lo, "lat": la})

for i, (lo, la) in enumerate(
    zip(
        [60, 80, 100, 120, 140, 145, 140, 130, 105, 100, 80, 60, 45, 30, 25, 30, 35, 50, 60],
        [55, 70, 75, 70, 55, 45, 35, 30, 0, 5, 10, 25, 30, 35, 42, 55, 70, 70, 55],
        strict=True,
    )
):
    continents.append({"continent": "Asia", "order": i, "lon": lo, "lat": la})

for i, (lo, la) in enumerate(
    zip(
        [113, 125, 135, 145, 152, 150, 140, 130, 115, 113],
        [-22, -15, -12, -15, -25, -38, -38, -33, -35, -22],
        strict=True,
    )
):
    continents.append({"continent": "Australia", "order": i, "lon": lo, "lat": la})

df_continents = pd.DataFrame(continents)

# Plot
plot = (
    ggplot()
    + geom_polygon(
        aes(x="lon", y="lat", group="continent"),
        data=df_continents,
        fill=LAND_FILL,
        color=LAND_BORDER,
        size=0.3,
        alpha=0.95,
    )
    + geom_path(
        aes(x="lon", y="lat", group="route_id", color="volume"), data=df_flights, size=0.85, alpha=0.55, lineend="round"
    )
    + geom_point(
        aes(x="lon", y="lat"), data=df_airports, color=INK_SOFT, fill=BRAND, size=3.5, shape="o", stroke=0.8, alpha=0.95
    )
    + scale_color_gradient(low="#009E73", high="#4467A3", name="Passengers\n(thousands/yr)")
    + coord_cartesian(xlim=(-180, 180), ylim=(-60, 80))
    + labs(title=TITLE, x="Longitude (°)", y="Latitude (°)")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.2, alpha=0.12),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        plot_title=element_text(size=TITLE_SIZE, color=INK, weight="bold"),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_position="right",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
