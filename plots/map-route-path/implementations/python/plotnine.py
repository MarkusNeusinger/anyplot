"""anyplot.ai
map-route-path: Route Path Map
Library: plotnine | Python 3.13
Quality: 91/100 | Created: 2026-01-19
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
PARK_FILL = "#C8E6C9" if THEME == "light" else "#1B3A1F"
PARK_COLOR = "#4CAF50" if THEME == "light" else "#388E3C"
LAKE_FILL = "#81D4FA" if THEME == "light" else "#0D3B52"
LAKE_COLOR = "#0288D1" if THEME == "light" else "#01579B"

# Data
np.random.seed(42)

base_lat = 47.82
base_lon = -121.75
n_points = 200
t = np.linspace(0, 2 * np.pi, n_points)

radius_lat = 0.08 + 0.02 * np.sin(3 * t)
radius_lon = 0.12 + 0.03 * np.cos(2 * t)
noise_lat = np.random.normal(0, 0.002, n_points)
noise_lon = np.random.normal(0, 0.003, n_points)

lat = base_lat + radius_lat * np.sin(t) + noise_lat
lon = base_lon + radius_lon * np.cos(t) + noise_lon

df_trail = pd.DataFrame({"lat": lat, "lon": lon, "sequence": range(n_points)})
df_trail["lat_smooth"] = df_trail["lat"].rolling(window=3, center=True, min_periods=1).mean()
df_trail["lon_smooth"] = df_trail["lon"].rolling(window=3, center=True, min_periods=1).mean()
df_trail["progress"] = df_trail["sequence"] / (n_points - 1) * 100

start_point = df_trail.iloc[[0]].copy()
end_point = df_trail.iloc[[-1]].copy()

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
    {"lon": park_boundary_lon, "lat": park_boundary_lat, "order": range(len(park_boundary_lon)), "area": "park"}
)

lake_t = np.linspace(0, 2 * np.pi, 20)
lake_lon = base_lon + 0.03 + 0.025 * np.cos(lake_t)
lake_lat = base_lat + 0.02 + 0.015 * np.sin(lake_t)
df_lake = pd.DataFrame({"lon": lake_lon, "lat": lake_lat, "order": range(len(lake_t)), "area": "lake"})

# Plot
plot = (
    ggplot()
    + geom_polygon(aes(x="lon", y="lat"), data=df_park, fill=PARK_FILL, color=PARK_COLOR, size=0.5, alpha=0.7)
    + geom_polygon(aes(x="lon", y="lat"), data=df_lake, fill=LAKE_FILL, color=LAKE_COLOR, size=0.4, alpha=0.8)
    + geom_path(
        aes(x="lon_smooth", y="lat_smooth", color="progress"), data=df_trail, size=2.5, alpha=0.85, lineend="round"
    )
    + geom_point(
        aes(x="lon_smooth", y="lat_smooth"),
        data=start_point,
        color="#2E7D32",
        fill="#4CAF50",
        size=5,
        shape="o",
        stroke=1.5,
    )
    + geom_point(
        aes(x="lon_smooth", y="lat_smooth"),
        data=end_point,
        color="#C62828",
        fill="#EF5350",
        size=5,
        shape="s",
        stroke=1.5,
    )
    + scale_color_gradient(low="#306998", high="#FFD43B", name="Trail Progress (%)")
    + coord_fixed(ratio=1.3)
    + labs(title="map-route-path · python · plotnine · anyplot.ai", x="Longitude (°)", y="Latitude (°)")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
