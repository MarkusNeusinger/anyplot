""" anyplot.ai
map-route-path: Route Path Map
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_viridis,
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
TERRAIN_BG = "#E8F0E4" if THEME == "light" else "#1D2419"

# Data — Swiss Alps hiking trail (GPS track simulation)
np.random.seed(42)
start_lat, start_lon = 46.85, 9.85
n_points = 150

t = np.linspace(0, 4 * np.pi, n_points)
lat_offset = np.cumsum(np.sin(t) * 0.002 + np.random.randn(n_points) * 0.0003)
lon_offset = np.cumsum(np.cos(t * 0.7) * 0.003 + np.random.randn(n_points) * 0.0004)

lat = start_lat + lat_offset
lon = start_lon + lon_offset
sequence = np.arange(n_points)

df = pd.DataFrame({"lat": lat, "lon": lon, "sequence": sequence, "progress": sequence / (n_points - 1) * 100})

start_pt = df.iloc[[0]].copy()
start_pt["marker"] = "Start"
end_pt = df.iloc[[-1]].copy()
end_pt["marker"] = "End"
markers_df = pd.concat([start_pt, end_pt], ignore_index=True)

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=TERRAIN_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor=element_line(color=INK_SOFT, size=0.15),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=10),
)

plot = (
    ggplot()
    + geom_path(
        aes(x="lon", y="lat", color="progress"),
        data=df,
        size=1.5,
        alpha=0.9,
        tooltips=layer_tooltips()
        .line("Progress|@progress%")
        .line("Lat|@lat")
        .line("Lon|@lon")
        .format("@progress", ".1f")
        .format("@lat", ".4f")
        .format("@lon", ".4f"),
    )
    + geom_point(
        aes(x="lon", y="lat", fill="marker"),
        data=markers_df,
        size=5,
        shape=21,
        stroke=2,
        color="white",
        tooltips=layer_tooltips().line("@marker"),
    )
    + scale_color_viridis(name="Progress (%)")
    + scale_fill_manual(values={"Start": "#009E73", "End": "#C475FD"}, name="Markers")
    + labs(x="Longitude (°)", y="Latitude (°)", title="map-route-path · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + coord_fixed(ratio=1.0)
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
