"""anyplot.ai
map-route-path: Route Path Map
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-21
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

# Plot
start_point = df.iloc[[0]]
end_point = df.iloc[[-1]]
plot = (
    ggplot()
    + geom_polygon(aes(x=LON, y=LAT), data=df_park, fill=PARK_FILL, color=PARK_COLOR, size=0.5, alpha=0.7)
    + geom_polygon(aes(x=LON, y=LAT), data=df_lake, fill=LAKE_FILL, color=LAKE_COLOR, size=0.4, alpha=0.8)
    + geom_path(aes(x=LON, y=LAT, color=PROGRESS), data=df, size=2.5, alpha=0.85, lineend="round")
    + geom_point(aes(x=LON, y=LAT), data=start_point, color=INK, fill=START_FILL, size=9, shape="o", stroke=1)
    + geom_point(aes(x=LON, y=LAT), data=end_point, color=INK, fill=END_FILL, size=3, shape="s", stroke=1)
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
