"""anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-19
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
    scale_alpha,
    scale_fill_gradient,
    scale_size,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave
from scipy.stats import gaussian_kde


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
# Imprint sequential ramp for continuous density (single polarity)
IMPRINT_SEQ = ("#009E73", "#4467A3")

# Constants: geography that stays true for any events in California
BANDWIDTH = 0.15  # KDE bandwidth factor, tuned to the geographic scale of the hot spots
GRID_SIZE = 80  # KDE grid resolution per axis
COAST = pd.DataFrame(
    {
        "lon": [-124.20, -124.16, -124.41, -124.35, -124.07, -123.80, -123.69, -123.05, -123.02, -122.51, -122.50]
        + [-122.03, -121.90, -121.90, -121.60, -121.28, -120.87, -120.90, -120.67, -120.65, -120.47, -119.70]
        + [-119.30, -119.10, -118.80, -118.50, -118.42, -118.30, -118.19, -117.90, -117.70, -117.38, -117.28]
        + [-117.24, -117.12, -116.10],
        "lat": [41.75, 40.80, 40.44, 40.25, 40.03, 39.40, 38.91, 38.30, 38.00, 37.78, 37.50]
        + [36.95, 36.60, 36.30, 36.00, 35.67, 35.37, 35.25, 34.90, 34.58, 34.45, 34.40]
        + [34.27, 34.09, 34.03, 34.01, 33.77, 33.71, 33.76, 33.60, 33.46, 33.20, 32.85]
        + [32.68, 32.53, 32.62],
    }
)
CITIES = pd.DataFrame({"lon": [-122.42, -118.25], "lat": [38.25, 34.55], "city": ["San Francisco", "Los Angeles"]})

# Columns: set these to your table's column names
LATITUDE = "Latitude"  # role: latitude
LONGITUDE = "Longitude"  # role: longitude
MAGNITUDE = "Magnitude"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("events.csv")
rng = np.random.default_rng(42)
n_cluster = 200
df = pd.DataFrame(
    {
        LATITUDE: np.concatenate(
            [rng.normal(34.05, 0.6, n_cluster), rng.normal(37.77, 0.4, n_cluster), rng.uniform(35.5, 37.5, n_cluster)]
        ),
        LONGITUDE: np.concatenate(
            [
                rng.normal(-118.25, 0.6, n_cluster),
                rng.normal(-122.42, 0.4, n_cluster),
                rng.uniform(-121.5, -119.5, n_cluster),
            ]
        ),
        MAGNITUDE: np.concatenate(
            [
                rng.exponential(2.0, n_cluster) + 1,
                rng.exponential(2.2, n_cluster) + 1.2,
                rng.exponential(1.5, n_cluster) + 0.8,
            ]
        ),
    }
)

# Plot: reads only df and the constants above
# Map window: the events' extent rounded outward to whole degrees
lon_min, lon_max = np.floor(df[LONGITUDE].min()), np.ceil(df[LONGITUDE].max())
lat_min, lat_max = np.floor(df[LATITUDE].min()), np.ceil(df[LATITUDE].max())

# KDE on a regular grid, scaled to 0-1 so the color bar reads sparse to dense
lon_mesh, lat_mesh = np.meshgrid(np.linspace(lon_min, lon_max, GRID_SIZE), np.linspace(lat_min, lat_max, GRID_SIZE))
kernel = gaussian_kde(np.vstack([df[LONGITUDE], df[LATITUDE]]), bw_method=BANDWIDTH)
density = kernel(np.vstack([lon_mesh.ravel(), lat_mesh.ravel()]))
DENSITY = "Relative event density"
df_grid = pd.DataFrame({LONGITUDE: lon_mesh.ravel(), LATITUDE: lat_mesh.ravel(), DENSITY: density / density.max()})

# Keep only the coastline inside the map window so nothing is drawn outside the panel
coast = COAST[COAST["lon"].between(lon_min, lon_max) & COAST["lat"].between(lat_min, lat_max)]

plot = (
    ggplot()
    + geom_contourf(aes(x=LONGITUDE, y=LATITUDE, z=DENSITY, fill="..level..", alpha="..level.."), data=df_grid, bins=12)
    + geom_path(aes(x="lon", y="lat"), data=coast, color=INK, size=0.8)
    + geom_point(
        aes(x=LONGITUDE, y=LATITUDE, size=MAGNITUDE),
        data=df,
        color=INK,
        fill=IMPRINT_PALETTE[0],
        alpha=0.55,
        shape=21,
        stroke=0.4,
        tooltips=layer_tooltips()
        .line(f"{LATITUDE}: @{{{LATITUDE}}}{{.2f}}")
        .line(f"{LONGITUDE}: @{{{LONGITUDE}}}{{.2f}}")
        .line(f"{MAGNITUDE}: @{{{MAGNITUDE}}}{{.1f}}"),
    )
    + geom_text(aes(x="lon", y="lat", label="city"), data=CITIES, color=INK, size=5, fontface="bold")
    + scale_fill_gradient(low=IMPRINT_SEQ[0], high=IMPRINT_SEQ[1], name="Relative\nevent density")
    + scale_alpha(range=[0.0, 0.85], guide="none")
    + scale_size(range=[1.5, 6], breaks=[2, 6, 10])
    + labs(
        x=LONGITUDE, y=LATITUDE, title="Seismic Activity Density · heatmap-geographic · python · letsplot · anyplot.ai"
    )
    + coord_fixed(ratio=1.0, xlim=[lon_min, lon_max], ylim=[lat_min, lat_max])
    + ggsize(600, 600)
    + theme_minimal()
    + theme(
        legend_position="bottom",
        legend_box="horizontal",
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=11, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=9, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major=element_line(color=GRID, size=0.3),
        panel_grid_minor=element_blank(),
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
