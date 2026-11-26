"""anyplot.ai
map-route-path: Route Path Map
Library: letsplot 4.11.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os
from itertools import pairwise

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_line,
    element_rect,
    element_text,
    geom_contour,
    geom_path,
    geom_point,
    geom_polygon,
    gggrid,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_gradientn,
    scale_fill_manual,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
GRID_MINOR = "rgba(26,26,23,0.05)" if THEME == "light" else "rgba(240,239,232,0.05)"
TERRAIN_BG = "#E8F0E4" if THEME == "light" else "#1D2419"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for marks (a colored line on the page), as (position, hex) stops
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Columns: set these to your table's column names
LAT = "Latitude (°)"  # role: lat
LON = "Longitude (°)"  # role: lon
SEQUENCE = "Sequence"  # role: sequence
PROGRESS = "Progress (%)"  # role: extra
MARKER = "Marker"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("track.csv")
# Swiss Alps hiking trail (GPS track simulation)
np.random.seed(42)
start_lat, start_lon = 46.85, 9.85
n_points = 150

t = np.linspace(0, 4 * np.pi, n_points)
lat_offset = np.cumsum(np.sin(t) * 0.002 + np.random.randn(n_points) * 0.0003)
lon_offset = np.cumsum(np.cos(t * 0.7) * 0.003 + np.random.randn(n_points) * 0.0004)

sequence = np.arange(n_points)
df = pd.DataFrame(
    {
        LAT: start_lat + lat_offset,
        LON: start_lon + lon_offset,
        SEQUENCE: sequence,
        PROGRESS: sequence / (n_points - 1) * 100,
    }
)

# Plot: reads only df and the constants above
df = df.sort_values(SEQUENCE)
markers_df = pd.concat([df.iloc[[0]].assign(**{MARKER: "Start"}), df.iloc[[-1]].assign(**{MARKER: "End"})])

# Terrain basemap drawn from the route's own extent: quiet contour lines of a smooth relief
# and a lake, both fixed-color layers so they stay below the route in visual weight
lon_lo, lon_hi = df[LON].min(), df[LON].max()
lat_lo, lat_hi = df[LAT].min(), df[LAT].max()
lon_pad, lat_pad = (lon_hi - lon_lo) * 0.12, (lat_hi - lat_lo) * 0.12
gx, gy = np.meshgrid(
    np.linspace(lon_lo - lon_pad, lon_hi + lon_pad, 90), np.linspace(lat_lo - lat_pad, lat_hi + lat_pad, 90)
)
u, v = (gx - lon_lo) / (lon_hi - lon_lo), (gy - lat_lo) / (lat_hi - lat_lo)
relief = (
    np.exp(-(((u - 0.2) / 0.35) ** 2 + ((v - 0.75) / 0.3) ** 2))
    + 0.8 * np.exp(-(((u - 0.8) / 0.3) ** 2 + ((v - 0.3) / 0.35) ** 2))
    + 0.15 * np.sin(5 * u) * np.cos(4 * v)
)
relief_df = pd.DataFrame({LON: gx.ravel(), LAT: gy.ravel(), "Relief": relief.ravel()})
angle = np.linspace(0, 2 * np.pi, 60)
lake_df = pd.DataFrame(
    {
        LON: lon_lo + (0.62 + 0.09 * np.cos(angle)) * (lon_hi - lon_lo),
        LAT: lat_lo + (0.78 + 0.06 * np.sin(angle)) * (lat_hi - lat_lo),
    }
)
CONTOUR = "rgba(26,26,23,0.22)" if THEME == "light" else "rgba(240,239,232,0.20)"
LAKE = "#CFE0E8" if THEME == "light" else "#223038"

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=TERRAIN_BG),
    panel_grid_major=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_line(color=GRID_MINOR, size=0.2),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=10),
)

plot = (
    ggplot()
    + geom_contour(aes(x=LON, y=LAT, z="Relief"), data=relief_df, bins=10, color=CONTOUR, size=0.4)
    + geom_polygon(aes(x=LON, y=LAT), data=lake_df, fill=LAKE, color=CONTOUR, size=0.4)
    + geom_path(
        aes(x=LON, y=LAT, color=PROGRESS),
        data=df,
        size=1.5,
        alpha=0.9,
        tooltips=layer_tooltips()
        .line(f"{PROGRESS}|@{{{PROGRESS}}}")
        .line(f"Lat|@{{{LAT}}}")
        .line(f"Lon|@{{{LON}}}")
        .format(f"@{{{PROGRESS}}}", ".1f")
        .format(f"@{{{LAT}}}", ".4f")
        .format(f"@{{{LON}}}", ".4f"),
    )
    + geom_point(
        aes(x=LON, y=LAT, fill=MARKER),
        data=markers_df,
        size=5,
        shape=21,
        stroke=2,
        color="white",
        tooltips=layer_tooltips().line(f"@{{{MARKER}}}"),
    )
    + scale_color_gradientn(colors=[ramp_color(SEQ_MARKS, k / 255) for k in range(256)], name=PROGRESS)
    + scale_fill_manual(values={"Start": IMPRINT_PALETTE[0], "End": IMPRINT_PALETTE[1]}, name="Markers")
    + labs(x=LON, y=LAT, title="map-route-path · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + coord_fixed(ratio=1.0)
)

# Fixed aspect leaves the canvas edges transparent: a one-panel grid paints the page color
plot = gggrid([plot]) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
