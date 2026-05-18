"""anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_contourf,
    geom_path,
    geom_point,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_viridis,
    scale_size,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave
from scipy.stats import gaussian_kde


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"

# Data — synthetic California seismic events clustered around major fault lines
np.random.seed(42)
n_points = 600

la_lat = np.random.normal(34.05, 0.6, n_points // 3)
la_lon = np.random.normal(-118.25, 0.6, n_points // 3)
la_magnitude = np.random.exponential(2.0, n_points // 3) + 1

sf_lat = np.random.normal(37.77, 0.4, n_points // 3)
sf_lon = np.random.normal(-122.42, 0.4, n_points // 3)
sf_magnitude = np.random.exponential(2.2, n_points // 3) + 1.2

cv_lat = np.random.uniform(35.5, 37.5, n_points // 3)
cv_lon = np.random.uniform(-121.5, -119.5, n_points // 3)
cv_magnitude = np.random.exponential(1.5, n_points // 3) + 0.8

latitude = np.concatenate([la_lat, sf_lat, cv_lat])
longitude = np.concatenate([la_lon, sf_lon, cv_lon])
magnitude = np.concatenate([la_magnitude, sf_magnitude, cv_magnitude])

df = pd.DataFrame({"latitude": latitude, "longitude": longitude, "magnitude": magnitude})

# KDE on a regular grid for the continuous density heatmap
lon_min, lon_max = -124, -116
lat_min, lat_max = 32, 40
n_grid = 80

lon_grid = np.linspace(lon_min, lon_max, n_grid)
lat_grid = np.linspace(lat_min, lat_max, n_grid)
lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

positions = np.vstack([longitude, latitude])
kernel = gaussian_kde(positions, bw_method=0.15)
grid_positions = np.vstack([lon_mesh.ravel(), lat_mesh.ravel()])
density = kernel(grid_positions).reshape(lon_mesh.shape)

df_grid = pd.DataFrame({"longitude": lon_mesh.flatten(), "latitude": lat_mesh.flatten(), "density": density.flatten()})

# City labels for geographic context
city_labels = pd.DataFrame({"lon": [-122.42, -118.25], "lat": [38.2, 34.5], "city": ["San Francisco", "Los Angeles"]})

# Simplified California coastline for geographic context
ca_coast = pd.DataFrame(
    {
        "lon": [-124.4, -124.2, -123.7, -122.4, -121.8, -120.6, -120.2, -118.5, -117.1, -117.0, -116.1],
        "lat": [40.3, 39.5, 38.9, 37.8, 37.0, 35.5, 34.5, 34.0, 32.5, 33.0, 32.7],
    }
)

# Plot
plot = (
    ggplot()
    + geom_contourf(aes(x="longitude", y="latitude", z="density", fill="..level.."), data=df_grid, bins=12, alpha=0.85)
    + geom_path(aes(x="lon", y="lat"), data=ca_coast, color=INK_SOFT, size=1.5)
    + geom_text(aes(x="lon", y="lat", label="city"), data=city_labels, color=INK, size=13, hjust=0.5, fontface="bold")
    + geom_point(
        aes(x="longitude", y="latitude", size="magnitude"),
        data=df,
        color="#0072B2",
        alpha=0.5,
        shape=21,
        fill="#E69F00",
        stroke=0.5,
        tooltips=layer_tooltips()
        .line("Lat: @latitude{.2f}")
        .line("Lon: @longitude{.2f}")
        .line("Magnitude: @magnitude{.1f}"),
    )
    + scale_fill_viridis(name="Event\nDensity")
    + scale_size(range=[2, 10], name="Magnitude")
    + labs(
        x="Longitude",
        y="Latitude",
        title="Seismic Activity Density · heatmap-geographic · python · letsplot · anyplot.ai",
    )
    + coord_fixed(ratio=1.0, xlim=[lon_min, lon_max], ylim=[lat_min, lat_max])
    + ggsize(1200, 1200)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=24, face="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=16, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major=element_line(color=RULE, size=0.5),
        panel_grid_minor=element_blank(),
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
