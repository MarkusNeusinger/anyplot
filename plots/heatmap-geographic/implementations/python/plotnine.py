""" pyplots.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
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
    geom_tile,
    ggplot,
    labs,
    scale_fill_gradient,
    theme,
    theme_minimal,
)
from scipy.ndimage import gaussian_filter
from scipy.stats import gaussian_kde


# Seed for reproducibility
np.random.seed(42)

# Generate synthetic geographic event data (earthquake events in Pacific Ring of Fire)

# Japan region cluster
japan_lon = np.random.normal(140, 3, 400)
japan_lat = np.random.normal(36, 4, 400)

# Indonesia region cluster
indo_lon = np.random.normal(115, 8, 350)
indo_lat = np.random.normal(-5, 4, 350)

# Chile/South America west coast
chile_lon = np.random.normal(-72, 2, 300)
chile_lat = np.random.normal(-30, 10, 300)

# California/US West Coast
calif_lon = np.random.normal(-120, 3, 250)
calif_lat = np.random.normal(37, 5, 250)

# Philippines cluster
phil_lon = np.random.normal(122, 3, 200)
phil_lat = np.random.normal(12, 4, 200)

# New Zealand region
nz_lon = np.random.normal(175, 3, 150)
nz_lat = np.random.normal(-40, 3, 150)

# Mediterranean seismic zone
med_lon = np.random.normal(25, 8, 200)
med_lat = np.random.normal(38, 3, 200)

# Additional scattered points
scatter_lon = np.random.uniform(-170, 170, 150)
scatter_lat = np.random.uniform(-50, 60, 150)

# Combine all clusters
all_lon = np.concatenate([japan_lon, indo_lon, chile_lon, calif_lon, phil_lon, nz_lon, med_lon, scatter_lon])
all_lat = np.concatenate([japan_lat, indo_lat, chile_lat, calif_lat, phil_lat, nz_lat, med_lat, scatter_lat])

# Compute 2D density on a grid for heatmap visualization
lon_grid = np.linspace(-180, 180, 120)
lat_grid = np.linspace(-60, 80, 70)
lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

# Kernel density estimation
points = np.vstack([all_lon, all_lat])
kde = gaussian_kde(points, bw_method=0.08)
density = kde(np.vstack([lon_mesh.ravel(), lat_mesh.ravel()]))
density = density.reshape(lon_mesh.shape)

# Apply Gaussian smoothing for smoother visualization
density = gaussian_filter(density, sigma=1.5)

# Create DataFrame for heatmap tiles
heatmap_data = []
for i in range(len(lat_grid)):
    for j in range(len(lon_grid)):
        heatmap_data.append({"longitude": lon_grid[j], "latitude": lat_grid[i], "density": density[i, j]})

df_heatmap = pd.DataFrame(heatmap_data)

# Filter out very low density values for cleaner visualization
threshold = df_heatmap["density"].quantile(0.3)
df_heatmap = df_heatmap[df_heatmap["density"] > threshold].copy()

# Simplified continent outlines for basemap
continents = []

# North America
na_lon = [
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
]
na_lat = [60, 65, 70, 55, 48, 33, 25, 26, 25, 35, 45, 48, 45, 27, 30, 20, 22, 50, 60, 55, 60]
for i in range(len(na_lon)):
    continents.append({"continent": "N. America", "order": i, "lon": na_lon[i], "lat": na_lat[i]})

# South America
sa_lon = [-80, -68, -60, -50, -35, -40, -50, -55, -68, -72, -75, -80, -82, -80]
sa_lat = [10, 12, 5, 0, -5, -22, -35, -52, -55, -18, -5, 0, 8, 10]
for i in range(len(sa_lon)):
    continents.append({"continent": "S. America", "order": i, "lon": sa_lon[i], "lat": sa_lat[i]})

# Europe
eu_lon = [-10, 0, 10, 20, 30, 40, 50, 60, 50, 35, 25, 20, 10, 0, -10, -10]
eu_lat = [35, 37, 36, 35, 35, 40, 45, 55, 70, 70, 70, 65, 60, 50, 40, 35]
for i in range(len(eu_lon)):
    continents.append({"continent": "Europe", "order": i, "lon": eu_lon[i], "lat": eu_lat[i]})

# Africa
af_lon = [-17, -5, 10, 35, 50, 52, 43, 35, 30, 15, 0, -17, -17]
af_lat = [15, 37, 37, 32, 12, 0, -25, -35, -35, -25, 5, 20, 15]
for i in range(len(af_lon)):
    continents.append({"continent": "Africa", "order": i, "lon": af_lon[i], "lat": af_lat[i]})

# Asia
as_lon = [60, 80, 100, 120, 140, 145, 140, 130, 105, 100, 80, 60, 45, 30, 25, 30, 35, 50, 60]
as_lat = [55, 70, 75, 70, 55, 45, 35, 30, 0, 5, 10, 25, 30, 35, 42, 55, 70, 70, 55]
for i in range(len(as_lon)):
    continents.append({"continent": "Asia", "order": i, "lon": as_lon[i], "lat": as_lat[i]})

# Australia
au_lon = [113, 125, 135, 145, 152, 150, 140, 130, 115, 113]
au_lat = [-22, -15, -12, -15, -25, -38, -38, -33, -35, -22]
for i in range(len(au_lon)):
    continents.append({"continent": "Australia", "order": i, "lon": au_lon[i], "lat": au_lat[i]})

df_continents = pd.DataFrame(continents)

# Create the geographic heatmap
plot = (
    ggplot()
    # Background ocean color
    + geom_tile(aes(x="longitude", y="latitude", fill="density"), data=df_heatmap, width=3.1, height=2.1, alpha=0.85)
    # Sequential colormap for density (YlOrRd-like)
    + scale_fill_gradient(low="#FFFFCC", high="#BD0026", name="Density")
    # Draw continent outlines (no fill, just borders for geographic context)
    + geom_polygon(aes(x="lon", y="lat", group="continent"), data=df_continents, fill="none", color="#404040", size=0.8)
    + coord_fixed(ratio=1.0, xlim=(-180, 180), ylim=(-60, 80))
    + labs(
        title="Seismic Activity Density · heatmap-geographic · plotnine · pyplots.ai",
        x="Longitude (°)",
        y="Latitude (°)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", size=0.3, alpha=0.4),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="#D4E8F7", alpha=0.6),
    )
)

# Save at 300 DPI for 4800x2700 px output
plot.save("plot.png", dpi=300, verbose=False)
