""" pyplots.ai
map-route-path: Route Path Map
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
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
    scale_color_gradient,
    theme,
    theme_minimal,
)


# Seed for reproducibility
np.random.seed(42)

# Simulate a hiking trail GPS track - Mountain Loop Trail
# Starting coordinates near a scenic mountain area
base_lat = 47.82
base_lon = -121.75

# Generate waypoints for a loop trail (200 waypoints)
n_points = 200
t = np.linspace(0, 2 * np.pi, n_points)

# Create a loop shape with some natural variation
# Base loop with varying radius to create an interesting trail shape
radius_lat = 0.08 + 0.02 * np.sin(3 * t)
radius_lon = 0.12 + 0.03 * np.cos(2 * t)

# Add GPS noise and terrain-following variation
noise_lat = np.random.normal(0, 0.002, n_points)
noise_lon = np.random.normal(0, 0.003, n_points)

# Generate coordinates
lat = base_lat + radius_lat * np.sin(t) + noise_lat
lon = base_lon + radius_lon * np.cos(t) + noise_lon

# Smooth the path slightly using rolling average for realistic GPS track
df_trail = pd.DataFrame({"lat": lat, "lon": lon, "sequence": range(n_points)})
df_trail["lat_smooth"] = df_trail["lat"].rolling(window=3, center=True, min_periods=1).mean()
df_trail["lon_smooth"] = df_trail["lon"].rolling(window=3, center=True, min_periods=1).mean()

# Calculate progress along trail (0 to 100%)
df_trail["progress"] = df_trail["sequence"] / (n_points - 1) * 100

# Start and end points
start_point = df_trail.iloc[[0]].copy()
end_point = df_trail.iloc[[-1]].copy()

# Create simplified terrain/area outline for context
# Represent a park boundary or natural area
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

# Create a small lake feature within the loop
lake_t = np.linspace(0, 2 * np.pi, 20)
lake_lon = base_lon + 0.03 + 0.025 * np.cos(lake_t)
lake_lat = base_lat + 0.02 + 0.015 * np.sin(lake_t)
df_lake = pd.DataFrame({"lon": lake_lon, "lat": lake_lat, "order": range(len(lake_t)), "area": "lake"})

# Build the route path visualization
plot = (
    ggplot()
    # Park area background
    + geom_polygon(aes(x="lon", y="lat"), data=df_park, fill="#C8E6C9", color="#4CAF50", size=0.5, alpha=0.7)
    # Lake feature
    + geom_polygon(aes(x="lon", y="lat"), data=df_lake, fill="#81D4FA", color="#0288D1", size=0.4, alpha=0.8)
    # Trail path with color gradient showing progress
    + geom_path(
        aes(x="lon_smooth", y="lat_smooth", color="progress"), data=df_trail, size=2.5, alpha=0.85, lineend="round"
    )
    # Start point (green circle)
    + geom_point(
        aes(x="lon_smooth", y="lat_smooth"),
        data=start_point,
        color="#2E7D32",
        fill="#4CAF50",
        size=8,
        shape="o",
        stroke=1.5,
    )
    # End point (red square)
    + geom_point(
        aes(x="lon_smooth", y="lat_smooth"),
        data=end_point,
        color="#C62828",
        fill="#EF5350",
        size=8,
        shape="s",
        stroke=1.5,
    )
    # Color scale for progress
    + scale_color_gradient(low="#306998", high="#FFD43B", name="Trail Progress (%)")
    # Fixed aspect ratio for geographic accuracy
    + coord_fixed(ratio=1.3)
    + labs(title="Mountain Loop Trail · map-route-path · plotnine · pyplots.ai", x="Longitude (°)", y="Latitude (°)")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=22, weight="bold"),
        axis_title=element_text(size=18),
        axis_text=element_text(size=14),
        legend_title=element_text(size=16),
        legend_text=element_text(size=12),
        legend_position="right",
        panel_grid_major=element_line(color="#E0E0E0", size=0.3),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#F5F5F5"),
    )
)

# Save at 300 DPI for 4800x2700 px output
plot.save("plot.png", dpi=300, verbose=False)
