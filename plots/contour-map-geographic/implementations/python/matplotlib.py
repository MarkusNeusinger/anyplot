""" pyplots.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-17
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon


# Data: Synthetic elevation data over Western US region
np.random.seed(42)

# Define geographic bounds (Western US)
lon_min, lon_max = -125, -105
lat_min, lat_max = 32, 49

# Create regular grid
n_points = 60
lons = np.linspace(lon_min, lon_max, n_points)
lats = np.linspace(lat_min, lat_max, n_points)
lon_grid, lat_grid = np.meshgrid(lons, lats)

# Generate synthetic elevation data with mountain ranges
# Base terrain
elevation = 500 + 300 * np.sin(np.radians(lon_grid) * 10) * np.cos(np.radians(lat_grid) * 8)

# Add mountain ranges (Sierra Nevada, Cascades, Rockies simulation)
# Sierra Nevada / Cascades (western edge)
sierra = 2500 * np.exp(-((lon_grid - (-121)) ** 2) / 8) * np.exp(-((lat_grid - 40) ** 2) / 100)
elevation += sierra

# Rocky Mountains (eastern edge)
rockies = 2800 * np.exp(-((lon_grid - (-108)) ** 2) / 12) * np.exp(-((lat_grid - 42) ** 2) / 150)
elevation += rockies

# Add some noise for realism
elevation += np.random.normal(0, 100, elevation.shape)
elevation = np.clip(elevation, 0, None)  # No negative elevations

# Simplified coastline points (Pacific Coast approximation)
coastline_lons = [
    -124.5,
    -124.2,
    -123.8,
    -124.0,
    -124.2,
    -123.5,
    -122.5,
    -121.5,
    -120.5,
    -120.0,
    -119.0,
    -118.0,
    -117.5,
]
coastline_lats = [49, 47, 45, 43, 42, 40, 38, 36.5, 35, 34.5, 34, 33.5, 32.5]

# State borders (simplified)
state_borders = [
    # Oregon-California border
    {"lons": [-124.2, -120, -117], "lats": [42, 42, 42]},
    # Oregon-Washington border
    {"lons": [-124.0, -120, -117], "lats": [46, 46, 46]},
    # Nevada-California border (partial)
    {"lons": [-120, -120, -117], "lats": [42, 39, 36]},
    # Idaho border (partial)
    {"lons": [-117, -117], "lats": [49, 42]},
]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Create filled contours (background)
levels = np.arange(0, 4500, 250)
filled_contours = ax.contourf(lon_grid, lat_grid, elevation, levels=levels, cmap="terrain", alpha=0.8, extend="max")

# Add contour lines
contour_lines = ax.contour(
    lon_grid,
    lat_grid,
    elevation,
    levels=levels[::2],  # Every other level for cleaner lines
    colors="#333333",
    linewidths=1.2,
)

# Add contour labels
ax.clabel(contour_lines, inline=True, fontsize=11, fmt="%d m")

# Draw Pacific Ocean (fill west of coastline)
ocean_lons = [-126, -126] + coastline_lons + [-117.5, -126]
ocean_lats = [49, 32] + coastline_lats + [32, 32]
ocean_poly = Polygon(
    list(zip(ocean_lons, ocean_lats, strict=True)), facecolor="#b0d0e8", edgecolor="none", alpha=0.9, zorder=2
)
ax.add_patch(ocean_poly)

# Draw coastline
ax.plot(coastline_lons, coastline_lats, color="#1a1a1a", linewidth=2.5, zorder=3)

# Draw state borders
for border in state_borders:
    ax.plot(border["lons"], border["lats"], color="#666666", linewidth=1, linestyle="--", zorder=3)

# Add colorbar
cbar = plt.colorbar(filled_contours, ax=ax, orientation="vertical", pad=0.02, shrink=0.85)
cbar.set_label("Elevation (m)", fontsize=18)
cbar.ax.tick_params(labelsize=14)

# Set axis labels and formatting
ax.set_xlabel("Longitude (°W)", fontsize=20)
ax.set_ylabel("Latitude (°N)", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Format tick labels to show degrees
ax.set_xticks(np.arange(-125, -104, 5))
ax.set_xticklabels([f"{abs(x)}°W" for x in np.arange(-125, -104, 5)])
ax.set_yticks(np.arange(32, 50, 4))
ax.set_yticklabels([f"{y}°N" for y in np.arange(32, 50, 4)])

# Add grid
ax.grid(True, alpha=0.4, linestyle="--", linewidth=0.8, zorder=1)

# Set axis limits
ax.set_xlim(lon_min, lon_max)
ax.set_ylim(lat_min, lat_max)
ax.set_aspect("equal")

# Title
ax.set_title("contour-map-geographic · matplotlib · pyplots.ai", fontsize=24, pad=15)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
