""" pyplots.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_text,
    geom_contourf,
    geom_path,
    geom_point,
    ggplot,
    ggsize,
    labs,
    scale_fill_gradient2,
    scale_size,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave
from scipy.stats import gaussian_kde


LetsPlot.setup_html()

# Generate synthetic earthquake/seismic event data for California region
np.random.seed(42)

# Create event clusters around major fault lines and cities
n_points = 600

# Los Angeles area cluster (high seismic activity)
la_lat = np.random.normal(34.05, 0.6, n_points // 3)
la_lon = np.random.normal(-118.25, 0.6, n_points // 3)
la_magnitude = np.random.exponential(2.0, n_points // 3) + 1

# San Francisco Bay area cluster
sf_lat = np.random.normal(37.77, 0.4, n_points // 3)
sf_lon = np.random.normal(-122.42, 0.4, n_points // 3)
sf_magnitude = np.random.exponential(2.2, n_points // 3) + 1.2

# Central California - scattered along fault line
cv_lat = np.random.uniform(35.5, 37.5, n_points // 3)
cv_lon = np.random.uniform(-121.5, -119.5, n_points // 3)
cv_magnitude = np.random.exponential(1.5, n_points // 3) + 0.8

# Combine all data
latitude = np.concatenate([la_lat, sf_lat, cv_lat])
longitude = np.concatenate([la_lon, sf_lon, cv_lon])
magnitude = np.concatenate([la_magnitude, sf_magnitude, cv_magnitude])

df = pd.DataFrame({"latitude": latitude, "longitude": longitude, "magnitude": magnitude})

# Create grid for KDE interpolation (density estimation)
lon_min, lon_max = -124, -116
lat_min, lat_max = 32, 40
n_grid = 80

lon_grid = np.linspace(lon_min, lon_max, n_grid)
lat_grid = np.linspace(lat_min, lat_max, n_grid)
lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

# Compute KDE for continuous density heatmap
positions = np.vstack([longitude, latitude])
kernel = gaussian_kde(positions, bw_method=0.15)
grid_positions = np.vstack([lon_mesh.ravel(), lat_mesh.ravel()])
density = kernel(grid_positions).reshape(lon_mesh.shape)

# Convert to long-form DataFrame for lets-plot
df_grid = pd.DataFrame({"longitude": lon_mesh.flatten(), "latitude": lat_mesh.flatten(), "density": density.flatten()})

# Simplified California coastline outline for geographic context
# Use path (line) for coastline outline without fill
ca_coast = pd.DataFrame(
    {
        "lon": [-124.4, -124.2, -123.7, -122.4, -121.8, -120.6, -120.2, -118.5, -117.1, -117.0, -116.1],
        "lat": [40.3, 39.5, 38.9, 37.8, 37.0, 35.5, 34.5, 34.0, 32.5, 33.0, 32.7],
    }
)

# Create geographic heatmap with density contours
plot = (
    ggplot()
    # Filled density contours for heatmap effect
    + geom_contourf(aes(x="longitude", y="latitude", z="density", fill="..level.."), data=df_grid, bins=12, alpha=0.85)
    # California coastline for geographic context
    + geom_path(aes(x="lon", y="lat"), data=ca_coast, color="#333333", size=1.5)
    # Scatter points showing actual events with size by magnitude
    + geom_point(
        aes(x="longitude", y="latitude", size="magnitude"),
        data=df,
        color="#306998",
        alpha=0.5,
        shape=21,
        fill="#FFD43B",
        stroke=0.5,
    )
    # Colorscale for density
    + scale_fill_gradient2(
        low="#FFFFD9", mid="#FD8D3C", high="#D73027", midpoint=density.max() * 0.5, name="Event\nDensity"
    )
    + scale_size(range=[2, 10], name="Magnitude")
    + labs(x="Longitude", y="Latitude", title="Seismic Activity Density · heatmap-geographic · letsplot · pyplots.ai")
    + coord_fixed(ratio=1.0, xlim=[lon_min, lon_max], ylim=[lat_min, lat_max])
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        panel_grid_major=element_line(color="#CCCCCC", size=0.3),
        panel_grid_minor=element_blank(),
    )
)

# Save as PNG (scale 3x for 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save interactive HTML
ggsave(plot, "plot.html", path=".")
