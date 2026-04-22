""" pyplots.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Simulated environmental monitoring stations across California
np.random.seed(42)

# Generate clustered point data simulating sensor locations
n_points = 500

# Create clusters representing different monitoring regions
# Central California coast cluster
coast_lat = np.random.normal(36.5, 0.8, n_points // 3)
coast_lon = np.random.normal(-121.5, 0.5, n_points // 3)

# Southern California cluster
socal_lat = np.random.normal(34.0, 0.6, n_points // 3)
socal_lon = np.random.normal(-118.0, 0.7, n_points // 3)

# Northern California cluster
norcal_lat = np.random.normal(38.5, 0.5, n_points // 3 + n_points % 3)
norcal_lon = np.random.normal(-122.5, 0.4, n_points // 3 + n_points % 3)

# Combine all clusters
latitudes = np.concatenate([coast_lat, socal_lat, norcal_lat])
longitudes = np.concatenate([coast_lon, socal_lon, norcal_lon])

# Measurement values (e.g., air quality index readings)
values = np.random.exponential(scale=50, size=len(latitudes)) + 20

# Define map boundaries for California
lat_min, lat_max = 32.5, 42.0
lon_min, lon_max = -125.0, -114.0

# Create 2D histogram for density estimation
grid_resolution = 150
lat_bins = np.linspace(lat_min, lat_max, grid_resolution)
lon_bins = np.linspace(lon_min, lon_max, grid_resolution)

# Compute weighted 2D histogram (density heatmap)
heatmap, lat_edges, lon_edges = np.histogram2d(
    latitudes, longitudes, bins=[lat_bins, lon_bins], weights=values, density=False
)

# Apply Gaussian smoothing for continuous appearance (KDE approximation)
# Create 1D Gaussian kernel
sigma = 3
kernel_size = int(6 * sigma + 1)
if kernel_size % 2 == 0:
    kernel_size += 1
kernel_x = np.arange(kernel_size) - kernel_size // 2
kernel_1d = np.exp(-(kernel_x**2) / (2 * sigma**2))
kernel_1d = kernel_1d / kernel_1d.sum()

# Apply separable 2D filter (convolve rows then columns)
heatmap_smooth = np.apply_along_axis(lambda row: np.convolve(row, kernel_1d, mode="same"), axis=0, arr=heatmap)
heatmap_smooth = np.apply_along_axis(lambda col: np.convolve(col, kernel_1d, mode="same"), axis=1, arr=heatmap_smooth)

# Mask zero/near-zero values for transparency
heatmap_masked = np.ma.masked_where(heatmap_smooth < 0.1, heatmap_smooth)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Add simple geographic context (California outline approximation)
# West coast line
coast_lons = [
    -124.4,
    -124.2,
    -123.8,
    -122.4,
    -122.0,
    -121.5,
    -121.0,
    -120.5,
    -120.0,
    -119.5,
    -119.0,
    -118.5,
    -118.0,
    -117.5,
    -117.2,
    -117.0,
    -117.1,
    -117.3,
]
coast_lats = [
    42.0,
    40.5,
    39.0,
    37.8,
    37.5,
    36.8,
    36.5,
    35.5,
    35.0,
    34.5,
    34.2,
    34.0,
    33.8,
    33.2,
    33.0,
    32.7,
    32.5,
    32.5,
]
ax.plot(coast_lons, coast_lats, "k-", linewidth=2, alpha=0.6, label="Coastline")

# Eastern border approximation
east_lons = [-117.3, -117.0, -116.5, -115.5, -114.6, -114.6, -120.0, -120.0, -121.0, -122.0, -123.0, -124.2, -124.4]
east_lats = [32.5, 33.0, 33.5, 34.0, 34.8, 36.0, 39.0, 40.0, 41.0, 41.5, 42.0, 42.0, 42.0]
ax.plot(east_lons, east_lats, "k-", linewidth=2, alpha=0.6)

# Draw heatmap
extent = [lon_min, lon_max, lat_min, lat_max]
im = ax.imshow(
    heatmap_masked.T, extent=extent, origin="lower", aspect="auto", cmap="YlOrRd", alpha=0.75, interpolation="bilinear"
)

# Scatter original points with low opacity to show data locations
ax.scatter(longitudes, latitudes, s=15, c="#306998", alpha=0.3, edgecolors="none", label="Sensor Locations")

# Colorbar
cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Air Quality Index (weighted density)", fontsize=18)
cbar.ax.tick_params(labelsize=14)

# Labels and styling
ax.set_xlabel("Longitude", fontsize=20)
ax.set_ylabel("Latitude", fontsize=20)
ax.set_title("heatmap-geographic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xlim(lon_min, lon_max)
ax.set_ylim(lat_min, lat_max)

# Add grid for geographic reference
ax.grid(True, alpha=0.3, linestyle="--")

# Legend
ax.legend(loc="upper right", fontsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
