"""anyplot.ai
map-route-path: Route Path Map
Library: plotnine 0.15.9 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os

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
    scale_color_gradientn,
    scale_fill_manual,
    scale_shape_manual,
    scale_size_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
PARK_FILL = "#C8E6C9" if THEME == "light" else "#2E5A33"
PARK_COLOR = "#4CAF50" if THEME == "light" else "#388E3C"
LAKE_FILL = "#81D4FA" if THEME == "light" else "#0D3B52"
LAKE_COLOR = "#0288D1" if THEME == "light" else "#01579B"
START_FILL = "#DDCC77"
END_FILL = "#AE3030"
CONTOUR_COLOR = "#8FB894" if THEME == "light" else "#4A7A50"
TRAIL_COLOR = "#B59A6A" if THEME == "light" else "#7A6A4A"
# Imprint sequential ramp for marks (colored lines on the page)
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants
BASE_LAT = 47.82
BASE_LON = -121.75
N_POINTS = 200

# Columns
LON = "Longitude (°)"  # role: x
LAT = "Latitude (°)"  # role: y
PROGRESS = "Trail Progress (%)"  # role: color
MARKER = "Route Marker"  # role: group

# Data
np.random.seed(42)

base_lat = BASE_LAT
base_lon = BASE_LON
n_points = N_POINTS
t = np.linspace(0, 2 * np.pi, n_points)

radius_lat = 0.08 + 0.02 * np.sin(3 * t)
radius_lon = 0.12 + 0.03 * np.cos(2 * t)
noise_lat = np.random.normal(0, 0.002, n_points)
noise_lon = np.random.normal(0, 0.003, n_points)

lat = base_lat + radius_lat * np.sin(t) + noise_lat
lon = base_lon + radius_lon * np.cos(t) + noise_lon

raw = pd.DataFrame({"lat": lat, "lon": lon})
df = pd.DataFrame(
    {
        LON: raw["lon"].rolling(window=3, center=True, min_periods=1).mean(),
        LAT: raw["lat"].rolling(window=3, center=True, min_periods=1).mean(),
        PROGRESS: np.arange(n_points) / (n_points - 1) * 100,
    }
)

park_boundary_lon = [
    base_lon - 0.20,
    base_lon - 0.18,
    base_lon - 0.10,
    base_lon + 0.05,
    base_lon + 0.15,
    base_lon + 0.18,
    base_lon + 0.15,
    base_lon + 0.05,
    base_lon - 0.08,
    base_lon - 0.18,
    base_lon - 0.20,
]
park_boundary_lat = [
    base_lat - 0.05,
    base_lat + 0.05,
    base_lat + 0.12,
    base_lat + 0.14,
    base_lat + 0.10,
    base_lat,
    base_lat - 0.10,
    base_lat - 0.12,
    base_lat - 0.10,
    base_lat - 0.08,
    base_lat - 0.05,
]
df_park = pd.DataFrame(
    {LON: park_boundary_lon, LAT: park_boundary_lat, "order": range(len(park_boundary_lon)), "area": "park"}
)

lake_t = np.linspace(0, 2 * np.pi, 20)
lake_lon = base_lon + 0.03 + 0.025 * np.cos(lake_t)
lake_lat = base_lat + 0.02 + 0.015 * np.sin(lake_t)
df_lake = pd.DataFrame({LON: lake_lon, LAT: lake_lat, "order": range(len(lake_t)), "area": "lake"})

# Terrain context: elevation contours around a summit and two side trails
contour_parts = []
for ring, scale in enumerate([0.25, 0.5, 0.75, 1.0, 1.3]):
    ang = np.linspace(0, 2 * np.pi, 80)
    contour_parts.append(
        pd.DataFrame(
            {
                LON: base_lon - 0.04 + scale * 0.07 * np.cos(ang) * (1 + 0.15 * np.sin(2 * ang)),
                LAT: base_lat + 0.01 + scale * 0.05 * np.sin(ang) * (1 + 0.12 * np.cos(3 * ang)),
                "ring": ring,
            }
        )
    )
df_contour = pd.concat(contour_parts, ignore_index=True)

trail_parts = []
for trail, (lon0, lat0, lon1, lat1) in enumerate([(-0.15, 0.10, -0.02, 0.02), (0.12, -0.09, 0.05, -0.01)]):
    s = np.linspace(0, 1, 30)
    trail_parts.append(
        pd.DataFrame(
            {
                LON: base_lon + lon0 + (lon1 - lon0) * s + 0.01 * np.sin(6 * np.pi * s),
                LAT: base_lat + lat0 + (lat1 - lat0) * s + 0.006 * np.cos(5 * np.pi * s),
                "trail": trail,
            }
        )
    )
df_trails = pd.concat(trail_parts, ignore_index=True)

# Start and end markers share one layer so the legend can name them
df_markers = pd.DataFrame(
    {MARKER: ["Start", "End"], LON: df[LON].iloc[[0, -1]].values, LAT: df[LAT].iloc[[0, -1]].values}
)
markers = df_markers[MARKER].tolist()

# Plot
plot = (
    ggplot()
    + geom_polygon(aes(x=LON, y=LAT), data=df_park, fill=PARK_FILL, color=PARK_COLOR, size=0.5, alpha=0.7)
    + geom_polygon(aes(x=LON, y=LAT), data=df_lake, fill=LAKE_FILL, color=LAKE_COLOR, size=0.4, alpha=0.8)
    + geom_path(aes(x=LON, y=LAT, group="ring"), data=df_contour, color=CONTOUR_COLOR, size=0.4, alpha=0.7)
    + geom_path(aes(x=LON, y=LAT, group="trail"), data=df_trails, color=TRAIL_COLOR, size=0.6, linetype="dashed")
    + geom_path(aes(x=LON, y=LAT, color=PROGRESS), data=df, size=2.5, alpha=0.85, lineend="round")
    + geom_point(aes(x=LON, y=LAT, fill=MARKER, shape=MARKER, size=MARKER), data=df_markers, color=INK, stroke=1)
    + scale_fill_manual(values=[START_FILL, END_FILL], limits=markers)
    + scale_shape_manual(values=["o", "s"], limits=markers)
    + scale_size_manual(values=[9, 3], limits=markers)
    + scale_color_gradientn(colors=[c for _, c in SEQ_MARKS], values=[p for p, _ in SEQ_MARKS])
    + coord_fixed(ratio=1.3)
    + labs(title="map-route-path · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
