""" pyplots.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
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
    geom_polygon,
    ggplot,
    labs,
    scale_fill_continuous,
    theme,
    theme_minimal,
)


# Seed for reproducibility
np.random.seed(42)

# Generate synthetic taxi pickup locations clustered around major urban centers
# Simulating taxi activity in a metropolitan region (e.g., NYC-like area)
n_points = 5000

# Multiple hotspots representing different zones
# Downtown core (high density)
downtown_lon = np.random.normal(-73.99, 0.02, n_points // 3)
downtown_lat = np.random.normal(40.75, 0.015, n_points // 3)

# Midtown area
midtown_lon = np.random.normal(-73.97, 0.025, n_points // 4)
midtown_lat = np.random.normal(40.78, 0.02, n_points // 4)

# Airport zone
airport_lon = np.random.normal(-73.79, 0.015, n_points // 5)
airport_lat = np.random.normal(40.65, 0.012, n_points // 5)

# Residential areas (scattered)
residential_lon = np.random.uniform(-74.05, -73.70, n_points // 4)
residential_lat = np.random.uniform(40.60, 40.85, n_points // 4)

# Combine all locations
lon = np.concatenate([downtown_lon, midtown_lon, airport_lon, residential_lon])
lat = np.concatenate([downtown_lat, midtown_lat, airport_lat, residential_lat])

# Create hexagonal bin polygons inline (no function)
gridsize = 25
lon_min, lon_max = lon.min() - 1, lon.max() + 1
lat_min, lat_max = lat.min() - 1, lat.max() + 1

# Flat-top hexagon geometry adapted for geographic coordinates
hex_width = (lon_max - lon_min) / gridsize
hex_radius = hex_width / np.sqrt(3)
row_height = hex_radius * 1.5

# Generate hex grid centers
centers = []
row = 0
y_pos = lat_min
while y_pos <= lat_max:
    x_offset = (hex_width / 2) if row % 2 else 0
    x_pos = lon_min + x_offset
    while x_pos <= lon_max:
        centers.append((x_pos, y_pos))
        x_pos += hex_width
    y_pos += row_height
    row += 1

# Count points per hexagon and create polygon vertices
points = np.column_stack([lon, lat])
records = []
hex_id = 0

for cx, cy in centers:
    # Point-in-hexagon test (flat-top)
    dx = np.abs(points[:, 0] - cx)
    dy = np.abs(points[:, 1] - cy)
    in_hex = (
        (dy <= hex_radius)
        & (dx <= hex_width / 2)
        & (hex_radius * hex_width / 2 >= dx * hex_radius + dy * hex_width / 4)
    )
    count = np.sum(in_hex)

    if count > 0:
        # Create hexagon vertices (flat-top orientation)
        angles = np.arange(6) * np.pi / 3 + np.pi / 6
        for angle in angles:
            records.append(
                {
                    "lon": cx + hex_radius * np.cos(angle),
                    "lat": cy + hex_radius * np.sin(angle),
                    "hex_id": hex_id,
                    "count": count,
                }
            )
        hex_id += 1

hex_df = pd.DataFrame(records)

# Simplified outline of the region (NYC-like coastline)
coastline_data = []

# Manhattan and surrounding area outline
coast_lon = [
    -74.05,
    -74.02,
    -73.97,
    -73.93,
    -73.90,
    -73.85,
    -73.75,
    -73.70,
    -73.70,
    -73.75,
    -73.80,
    -73.85,
    -73.90,
    -73.95,
    -74.00,
    -74.05,
    -74.05,
]
coast_lat = [
    40.55,
    40.50,
    40.52,
    40.55,
    40.60,
    40.65,
    40.70,
    40.75,
    40.85,
    40.90,
    40.88,
    40.85,
    40.80,
    40.75,
    40.65,
    40.60,
    40.55,
]

for i in range(len(coast_lon)):
    coastline_data.append({"region": "land", "order": i, "lon": coast_lon[i], "lat": coast_lat[i]})

df_coastline = pd.DataFrame(coastline_data)

# Create the hexbin map with geographic context
plot = (
    ggplot()
    # Draw coastline/land boundary as basemap context
    + geom_polygon(
        aes(x="lon", y="lat", group="region"), data=df_coastline, fill="#E8E8E8", color="#999999", size=0.8, alpha=0.6
    )
    # Draw hexagonal bins colored by density
    + geom_polygon(
        aes(x="lon", y="lat", group="hex_id", fill="count"), data=hex_df, color="white", size=0.2, alpha=0.85
    )
    # Sequential colormap for density (viridis)
    + scale_fill_continuous(cmap_name="YlOrRd", name="Pickup Count")
    # Fixed aspect ratio for geographic accuracy
    + coord_fixed(ratio=1.0, xlim=(-74.08, -73.68), ylim=(40.52, 40.92))
    + labs(title="hexbin-map-geographic · plotnine · pyplots.ai", x="Longitude (°)", y="Latitude (°)")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major=element_line(color="#888888", size=0.5, alpha=0.3),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#D4E8F7", alpha=0.4),
    )
)

# Save at 300 DPI for 4800x2700 px output
plot.save("plot.png", dpi=300)
