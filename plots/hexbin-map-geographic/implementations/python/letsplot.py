"""anyplot.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: letsplot | Python 3.13
Quality: pending | Updated: 2026-05-27
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
    geom_hex,
    geom_polygon,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_gradient,
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BASEMAP_FILL = "#E4E4DC" if THEME == "light" else "#2E2E2A"
BASEMAP_COLOR = "#AAAAAA" if THEME == "light" else "#5A5A54"

# Data: Simulated taxi pickup locations in New York City area
np.random.seed(42)
n_points = 15000

manhattan_lat = np.random.normal(40.758, 0.025, n_points // 2)
manhattan_lon = np.random.normal(-73.985, 0.015, n_points // 2)

midtown_lat = np.random.normal(40.752, 0.018, n_points // 4)
midtown_lon = np.random.normal(-73.972, 0.012, n_points // 4)

jfk_lat = np.random.normal(40.641, 0.012, n_points // 6)
jfk_lon = np.random.normal(-73.778, 0.015, n_points // 6)

lga_lat = np.random.normal(40.773, 0.008, n_points // 12)
lga_lon = np.random.normal(-73.872, 0.010, n_points // 12)

latitude = np.concatenate([manhattan_lat, midtown_lat, jfk_lat, lga_lat])
longitude = np.concatenate([manhattan_lon, midtown_lon, jfk_lon, lga_lon])

df = pd.DataFrame({"lat": latitude, "lon": longitude})

# Simplified basemap: NYC borough outlines for geographic context
manhattan_outline = pd.DataFrame(
    {
        "lon": [-74.02, -73.97, -73.93, -73.91, -73.93, -73.97, -74.01, -74.02],
        "lat": [40.70, 40.71, 40.78, 40.82, 40.88, 40.80, 40.73, 40.70],
        "borough": ["Manhattan"] * 8,
        "order": list(range(8)),
    }
)

brooklyn_outline = pd.DataFrame(
    {
        "lon": [-74.04, -73.95, -73.85, -73.83, -73.86, -73.95, -74.03, -74.04],
        "lat": [40.57, 40.57, 40.58, 40.64, 40.70, 40.70, 40.64, 40.57],
        "borough": ["Brooklyn"] * 8,
        "order": list(range(8)),
    }
)

queens_outline = pd.DataFrame(
    {
        "lon": [-73.96, -73.82, -73.70, -73.72, -73.76, -73.85, -73.93, -73.96],
        "lat": [40.70, 40.60, 40.60, 40.73, 40.80, 40.81, 40.78, 40.70],
        "borough": ["Queens"] * 8,
        "order": list(range(8)),
    }
)

df_boroughs = pd.concat([manhattan_outline, brooklyn_outline, queens_outline], ignore_index=True)

# Title — scale fontsize for length
title = "NYC Taxi Pickups · hexbin-map-geographic · python · letsplot · anyplot.ai"
title_size = max(11, round(16 * 67 / len(title)))

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_MUTED, size=0.2),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    plot_title=element_text(color=INK, size=title_size),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=11),
    legend_position="right",
)

plot = (
    ggplot()
    + geom_polygon(
        aes(x="lon", y="lat", group="borough"),
        data=df_boroughs,
        fill=BASEMAP_FILL,
        color=BASEMAP_COLOR,
        size=0.6,
        alpha=0.7,
    )
    + geom_hex(
        aes(x="lon", y="lat"), data=df, bins=[40, 40], alpha=0.85, tooltips=layer_tooltips().line("Pickups|@..count..")
    )
    + scale_fill_gradient(low="#009E73", high="#4467A3", name="Pickup\nCount")
    + labs(x="Longitude (°)", y="Latitude (°)", title=title)
    + coord_fixed(ratio=1.0, xlim=[-74.05, -73.68], ylim=[40.55, 40.90])
    + ggsize(800, 450)
    + theme_minimal()
    + anyplot_theme
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
