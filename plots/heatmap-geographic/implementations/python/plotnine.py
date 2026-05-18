"""anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: plotnine | Python 3.13
Quality: pending | Updated: 2026-05-18
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
OCEAN_BG = "#D4E8F7" if THEME == "light" else "#1A2A3A"
CONTINENT_COLOR = "#505050" if THEME == "light" else "#A0A09A"

# Data
np.random.seed(42)

# Generate synthetic earthquake event data (Pacific Ring of Fire and major seismic zones)

japan_lon = np.random.normal(140, 3, 400)
japan_lat = np.random.normal(36, 4, 400)

indo_lon = np.random.normal(115, 8, 350)
indo_lat = np.random.normal(-5, 4, 350)

chile_lon = np.random.normal(-72, 2, 300)
chile_lat = np.random.normal(-30, 10, 300)

calif_lon = np.random.normal(-120, 3, 250)
calif_lat = np.random.normal(37, 5, 250)

phil_lon = np.random.normal(122, 3, 200)
phil_lat = np.random.normal(12, 4, 200)

nz_lon = np.random.normal(175, 3, 150)
nz_lat = np.random.normal(-40, 3, 150)

med_lon = np.random.normal(25, 8, 200)
med_lat = np.random.normal(38, 3, 200)

scatter_lon = np.random.uniform(-170, 170, 150)
scatter_lat = np.random.uniform(-50, 60, 150)

all_lon = np.concatenate([japan_lon, indo_lon, chile_lon, calif_lon, phil_lon, nz_lon, med_lon, scatter_lon])
all_lat = np.concatenate([japan_lat, indo_lat, chile_lat, calif_lat, phil_lat, nz_lat, med_lat, scatter_lat])

# Kernel density estimation on a geographic grid
lon_grid = np.linspace(-180, 180, 120)
lat_grid = np.linspace(-60, 80, 70)
lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

points = np.vstack([all_lon, all_lat])
kde = gaussian_kde(points, bw_method=0.08)
density = kde(np.vstack([lon_mesh.ravel(), lat_mesh.ravel()]))
density = density.reshape(lon_mesh.shape)
density = gaussian_filter(density, sigma=1.5)

heatmap_rows = []
for i in range(len(lat_grid)):
    for j in range(len(lon_grid)):
        heatmap_rows.append({"longitude": lon_grid[j], "latitude": lat_grid[i], "density": density[i, j]})

df_heatmap = pd.DataFrame(heatmap_rows)

# Filter low-density ocean tiles to show clear hotspots only
threshold = df_heatmap["density"].quantile(0.45)
df_heatmap = df_heatmap[df_heatmap["density"] > threshold].copy()

# Simplified continent outlines for geographic context
continents = []

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

sa_lon = [-80, -68, -60, -50, -35, -40, -50, -55, -68, -72, -75, -80, -82, -80]
sa_lat = [10, 12, 5, 0, -5, -22, -35, -52, -55, -18, -5, 0, 8, 10]
for i in range(len(sa_lon)):
    continents.append({"continent": "S. America", "order": i, "lon": sa_lon[i], "lat": sa_lat[i]})

eu_lon = [-10, 0, 10, 20, 30, 40, 50, 60, 50, 35, 25, 20, 10, 0, -10, -10]
eu_lat = [35, 37, 36, 35, 35, 40, 45, 55, 70, 70, 70, 65, 60, 50, 40, 35]
for i in range(len(eu_lon)):
    continents.append({"continent": "Europe", "order": i, "lon": eu_lon[i], "lat": eu_lat[i]})

af_lon = [-17, -5, 10, 35, 50, 52, 43, 35, 30, 15, 0, -17, -17]
af_lat = [15, 37, 37, 32, 12, 0, -25, -35, -35, -25, 5, 20, 15]
for i in range(len(af_lon)):
    continents.append({"continent": "Africa", "order": i, "lon": af_lon[i], "lat": af_lat[i]})

as_lon = [60, 80, 100, 120, 140, 145, 140, 130, 105, 100, 80, 60, 45, 30, 25, 30, 35, 50, 60]
as_lat = [55, 70, 75, 70, 55, 45, 35, 30, 0, 5, 10, 25, 30, 35, 42, 55, 70, 70, 55]
for i in range(len(as_lon)):
    continents.append({"continent": "Asia", "order": i, "lon": as_lon[i], "lat": as_lat[i]})

au_lon = [113, 125, 135, 145, 152, 150, 140, 130, 115, 113]
au_lat = [-22, -15, -12, -15, -25, -38, -38, -33, -35, -22]
for i in range(len(au_lon)):
    continents.append({"continent": "Australia", "order": i, "lon": au_lon[i], "lat": au_lat[i]})

df_continents = pd.DataFrame(continents)

# Plot
plot = (
    ggplot()
    + geom_tile(aes(x="longitude", y="latitude", fill="density"), data=df_heatmap, width=3.1, height=2.1, alpha=0.90)
    + scale_fill_gradient(low="#FFFFCC", high="#BD0026", name="Density")
    + geom_polygon(
        aes(x="lon", y="lat", group="continent"), data=df_continents, fill="none", color=CONTINENT_COLOR, size=0.8
    )
    + coord_fixed(ratio=1.0, xlim=(-180, 180), ylim=(-60, 80))
    + labs(
        title="Seismic Activity Density · heatmap-geographic · python · plotnine · anyplot.ai",
        x="Longitude (°)",
        y="Latitude (°)",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=OCEAN_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, weight="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=14, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
