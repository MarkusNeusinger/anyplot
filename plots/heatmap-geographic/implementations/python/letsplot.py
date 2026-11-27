"""anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-26
"""

import math
import os
from itertools import pairwise

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
    gggrid,
    ggplot,
    ggsize,
    ggtb,
    labs,
    layer_tooltips,
    scale_fill_gradientn,
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
RULE = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for filled fields, as (position, hex) stops, low -> high
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Constants: California reference geography (coastline, city labels) and KDE settings
BANDWIDTH = 0.15  # gaussian_kde bandwidth factor
GRID_SIZE = 80  # KDE grid resolution per axis
MAP_PAD = 1.0  # degrees of map around the events
CA_COAST = pd.DataFrame(
    {
        "lon": [-124.21, -124.20, -124.10, -124.41, -124.35, -123.78, -123.70, -123.10, -123.05, -122.97]
        + [-122.51, -122.50, -122.30, -122.00, -121.80, -121.90, -121.90, -121.50, -121.28, -120.87]
        + [-120.65, -120.47, -119.70, -119.20, -118.80, -118.50, -118.40, -118.30, -117.90, -117.60]
        + [-117.40, -117.27, -117.20, -117.12],
        "lat": [42.00, 41.75, 41.00, 40.44, 40.25, 39.50, 39.00, 38.50, 38.30, 38.00]
        + [37.80, 37.50, 37.10, 36.95, 36.80, 36.60, 36.30, 36.00, 35.67, 35.35]
        + [34.90, 34.45, 34.40, 34.15, 34.03, 34.00, 33.85, 33.73, 33.60, 33.40]
        + [33.20, 32.85, 32.70, 32.53],
    }
)
CITIES = pd.DataFrame({"lon": [-122.42, -118.25], "lat": [39.0, 36.3], "city": ["San Francisco", "Los Angeles"]})

# Columns: set these to your table's column names
LATITUDE = "Latitude"  # role: latitude
LONGITUDE = "Longitude"  # role: longitude
MAGNITUDE = "Magnitude"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("events.csv")
# Synthetic California seismic events clustered around major fault lines
np.random.seed(42)
n_points = 600

la_lat = np.random.normal(34.05, 0.6, n_points // 3)
la_lon = np.random.normal(-118.25, 0.6, n_points // 3)
la_magnitude = np.random.exponential(1.0, n_points // 3) + 1.5

sf_lat = np.random.normal(37.77, 0.4, n_points // 3)
sf_lon = np.random.normal(-122.42, 0.4, n_points // 3)
sf_magnitude = np.random.exponential(1.2, n_points // 3) + 1.8

cv_lat = np.random.uniform(35.5, 37.5, n_points // 3)
cv_lon = np.random.uniform(-121.5, -119.5, n_points // 3)
cv_magnitude = np.random.exponential(0.9, n_points // 3) + 1.2

df = pd.DataFrame(
    {
        LATITUDE: np.concatenate([la_lat, sf_lat, cv_lat]),
        LONGITUDE: np.concatenate([la_lon, sf_lon, cv_lon]),
        MAGNITUDE: np.concatenate([la_magnitude, sf_magnitude, cv_magnitude]),
    }
)

# Plot: reads only df and the constants above
lon_min, lon_max = df[LONGITUDE].min() - MAP_PAD, df[LONGITUDE].max() + MAP_PAD
lat_min, lat_max = df[LATITUDE].min() - MAP_PAD, df[LATITUDE].max() + MAP_PAD
# Widen the shorter range to the longer one so the fixed-aspect map fills the square canvas
span = max(lon_max - lon_min, lat_max - lat_min)
lon_mid, lat_mid = (lon_min + lon_max) / 2, (lat_min + lat_max) / 2
lon_min, lon_max = lon_mid - span / 2, lon_mid + span / 2
lat_min, lat_max = lat_mid - span / 2, lat_mid + span / 2

# KDE on a regular grid for the continuous density heatmap
lon_mesh, lat_mesh = np.meshgrid(np.linspace(lon_min, lon_max, GRID_SIZE), np.linspace(lat_min, lat_max, GRID_SIZE))
kernel = gaussian_kde(df[[LONGITUDE, LATITUDE]].dropna().to_numpy().T, bw_method=BANDWIDTH)
density = kernel(np.vstack([lon_mesh.ravel(), lat_mesh.ravel()])).reshape(lon_mesh.shape)
df_grid = pd.DataFrame({LONGITUDE: lon_mesh.ravel(), LATITUDE: lat_mesh.ravel(), "density": density.ravel()})

plot = (
    ggplot()
    + geom_contourf(aes(x=LONGITUDE, y=LATITUDE, z="density", fill="..level.."), data=df_grid, bins=12, alpha=0.85)
    + geom_path(aes(x="lon", y="lat"), data=CA_COAST, color=INK_SOFT, size=1.0)
    + geom_text(aes(x="lon", y="lat", label="city"), data=CITIES, color=INK, size=5, hjust=0.5, fontface="bold")
    + geom_point(
        aes(x=LONGITUDE, y=LATITUDE, size=MAGNITUDE),
        data=df,
        color=IMPRINT_PALETTE[2],
        alpha=0.25,
        shape=21,
        fill=IMPRINT_PALETTE[4],
        stroke=0.5,
        tooltips=layer_tooltips()
        .line(f"Lat: @{{{LATITUDE}}}{{.2f}}")
        .line(f"Lon: @{{{LONGITUDE}}}{{.2f}}")
        .line(f"Magnitude: @{{{MAGNITUDE}}}{{.1f}}"),
    )
    + scale_fill_gradientn(colors=[ramp_color(SEQ_FIELDS, k / 255) for k in range(256)], name="Event\nDensity")
    + scale_size(range=[1, 4], name=MAGNITUDE)
    + labs(
        x=LONGITUDE, y=LATITUDE, title="Seismic Activity Density · heatmap-geographic · python · letsplot · anyplot.ai"
    )
    + coord_fixed(ratio=1.0, xlim=[lon_min, lon_max], ylim=[lat_min, lat_max])
    + ggtb()
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=11, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="bottom",
        panel_grid_major=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
    )
)

# The fixed aspect leaves transparent strips: a one-panel grid paints the whole square canvas
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
