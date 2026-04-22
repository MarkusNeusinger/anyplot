""" pyplots.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-17
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_line,
    element_text,
    geom_contour,
    geom_contourf,
    geom_path,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_gradient2,
    theme,
    theme_bw,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Create synthetic elevation data for a geographic region (Western US mountains)
np.random.seed(42)

# Grid covering a region (e.g., mountain range area)
lat_range = np.linspace(35, 45, 50)  # Latitude range
lon_range = np.linspace(-120, -105, 60)  # Longitude range
lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)

# Generate realistic elevation data with mountain peaks
elevation = np.zeros_like(lat_grid)

# Add several mountain peaks with realistic elevations for Western US
peaks = [
    (40.5, -111.5, 2800, 2.0),  # Peak near Salt Lake City (Wasatch Range ~3400m)
    (39.0, -114.0, 2600, 1.8),  # Nevada peak (Great Basin ~3000m)
    (43.5, -110.5, 3200, 2.5),  # Tetons area (~4200m Grand Teton)
    (37.5, -118.5, 3500, 2.2),  # Sierra Nevada (~4400m Mt Whitney)
    (41.0, -106.5, 2900, 2.0),  # Colorado peak (Rocky Mountains ~4300m)
]

for peak_lat, peak_lon, peak_height, spread in peaks:
    distance = np.sqrt((lat_grid - peak_lat) ** 2 + (lon_grid - peak_lon) ** 2)
    elevation += peak_height * np.exp(-(distance**2) / (2 * spread**2))

# Add base elevation (Great Basin floor ~1200m) and some noise
elevation += 1200 + np.random.randn(*elevation.shape) * 30

# Flatten for lets-plot
df = pd.DataFrame({"lon": lon_grid.flatten(), "lat": lat_grid.flatten(), "elevation": elevation.flatten()})

# Calculate actual elevation range for proper color scale
elev_min = int(np.floor(elevation.min() / 500) * 500)  # Round down to nearest 500
elev_max = int(np.ceil(elevation.max() / 500) * 500)  # Round up to nearest 500
elev_mid = (elev_min + elev_max) / 2

# Define contour levels for labeling (every 1000m for cleaner labels)
contour_levels = [2000, 3000, 4000, 5000, 6000]

# Create contour label positions - find best spots for each level
label_data = []
used_positions = []

for level in contour_levels:
    # Find all points near this contour level
    candidates = df[abs(df["elevation"] - level) < 75].copy()
    if len(candidates) == 0:
        continue

    # Find a position that's not too close to existing labels
    best_candidate = None
    best_dist = 0

    for _, row in candidates.iterrows():
        min_dist = float("inf")
        for used_lon, used_lat in used_positions:
            dist = np.sqrt((row["lon"] - used_lon) ** 2 + (row["lat"] - used_lat) ** 2)
            min_dist = min(min_dist, dist)

        if len(used_positions) == 0 or min_dist > best_dist:
            best_dist = min_dist
            best_candidate = row

    if best_candidate is not None and (len(used_positions) == 0 or best_dist > 3):
        label_data.append({"lon": best_candidate["lon"], "lat": best_candidate["lat"], "label": f"{int(level)}m"})
        used_positions.append((best_candidate["lon"], best_candidate["lat"]))

label_df = pd.DataFrame(label_data) if label_data else pd.DataFrame({"lon": [], "lat": [], "label": []})

# Create simplified geographic boundary (approximate Pacific coastline)
coast_lons = [-120, -120, -120, -120, -119.5, -119, -118.5, -118]
coast_lats = [35, 37, 39, 41, 42, 43, 44, 45]
coast_df = pd.DataFrame({"lon": coast_lons, "lat": coast_lats})

# Create state border approximations (simplified)
border_segments = [
    # CA-NV border (approx)
    {"lon": [-120, -120, -117, -114], "lat": [42, 39, 36, 35]},
    # NV-UT border (approx)
    {"lon": [-114, -114], "lat": [35, 42]},
    # UT-WY border (approx)
    {"lon": [-111, -111], "lat": [41, 45]},
    # ID-MT border (approx)
    {"lon": [-117, -111], "lat": [45, 45]},
]

border_dfs = [pd.DataFrame(seg) for seg in border_segments]

# Create contour plot with filled regions
plot = (
    ggplot(df, aes(x="lon", y="lat", z="elevation"))
    + geom_contourf(aes(fill="..level.."), bins=12, alpha=0.9)
    + geom_contour(color="#333333", size=0.5, bins=12, alpha=0.7)
    + scale_fill_gradient2(
        low="#1a5e1a",
        mid="#c4a35a",
        high="#f5f5f5",
        midpoint=elev_mid,
        limits=[elev_min, elev_max],
        name="Elevation (m)",
    )
    # Add coastline
    + geom_path(data=coast_df, mapping=aes(x="lon", y="lat"), color="#0066cc", size=1.5, alpha=0.8, inherit_aes=False)
)

# Add state borders
for border_df in border_dfs:
    plot = plot + geom_path(
        data=border_df, mapping=aes(x="lon", y="lat"), color="#666666", size=0.8, linetype="dashed", inherit_aes=False
    )

# Add contour labels if we have any
if len(label_df) > 0:
    plot = plot + geom_text(
        data=label_df,
        mapping=aes(x="lon", y="lat", label="label"),
        color="#222222",
        size=10,
        fontface="bold",
        inherit_aes=False,
    )

# Add styling and theme
plot = (
    plot
    + labs(title="contour-map-geographic · letsplot · pyplots.ai", x="Longitude (°W)", y="Latitude (°N)")
    + theme_bw()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major=element_line(color="#cccccc", size=0.3),
        panel_grid_minor=element_line(color="#eeeeee", size=0.2),
    )
    + ggsize(1600, 900)
    + coord_fixed(ratio=1.0)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
