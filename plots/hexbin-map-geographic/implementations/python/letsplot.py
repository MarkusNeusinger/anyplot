"""anyplot.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-06-16
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
    geom_hex,
    geom_polygon,
    gggrid,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_gradientn,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BASEMAP_FILL = "#E4E4DC" if THEME == "light" else "#2E2E2A"
BASEMAP_COLOR = "#AAAAAA" if THEME == "light" else "#5A5A54"

# Imprint sequential ramp for fields (colored cells filling the plot), per theme
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
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


LetsPlot.setup_html()

# Constants
N_BINS = 40  # hexagons per axis: balances detail against aggregation

# Columns
LAT = "lat"  # role: lat
LON = "lon"  # role: lon

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

df = pd.DataFrame({LAT: latitude, LON: longitude})

# Plot
# Simplified basemap: faithful NYC borough outlines for geographic context.
# Vertices trace the real coastlines of each borough (narrow Manhattan island,
# Brooklyn's south/west waterfront, Queens' large NE landmass) so the clusters
# sit plausibly inside their nominal borough.
manhattan_lon_outline = [
    -74.015,
    -74.013,
    -74.009,
    -73.993,
    -73.972,
    -73.948,
    -73.934,
    -73.910,
    -73.920,
    -73.929,
    -73.937,
    -73.958,
    -73.971,
    -73.973,
    -73.978,
    -74.000,
    -74.015,
]
manhattan_lat_outline = [
    40.701,
    40.731,
    40.756,
    40.782,
    40.800,
    40.829,
    40.850,
    40.872,
    40.866,
    40.834,
    40.806,
    40.776,
    40.752,
    40.733,
    40.711,
    40.703,
    40.701,
]
manhattan_outline = pd.DataFrame(
    {
        LON: manhattan_lon_outline,
        LAT: manhattan_lat_outline,
        "borough": ["Manhattan"] * len(manhattan_lon_outline),
        "order": list(range(len(manhattan_lon_outline))),
    }
)

brooklyn_lon_outline = [
    -74.025,
    -74.012,
    -73.998,
    -73.972,
    -73.934,
    -73.866,
    -73.858,
    -73.866,
    -73.926,
    -73.978,
    -74.010,
    -74.025,
]
brooklyn_lat_outline = [40.633, 40.640, 40.700, 40.704, 40.739, 40.694, 40.668, 40.629, 40.575, 40.574, 40.602, 40.633]
brooklyn_outline = pd.DataFrame(
    {
        LON: brooklyn_lon_outline,
        LAT: brooklyn_lat_outline,
        "borough": ["Brooklyn"] * len(brooklyn_lon_outline),
        "order": list(range(len(brooklyn_lon_outline))),
    }
)

queens_lon_outline = [
    -73.962,
    -73.910,
    -73.840,
    -73.765,
    -73.700,
    -73.736,
    -73.760,
    -73.823,
    -73.866,
    -73.866,
    -73.934,
    -73.962,
]
queens_lat_outline = [40.741, 40.779, 40.792, 40.789, 40.745, 40.660, 40.605, 40.583, 40.629, 40.694, 40.739, 40.741]
queens_outline = pd.DataFrame(
    {
        LON: queens_lon_outline,
        LAT: queens_lat_outline,
        "borough": ["Queens"] * len(queens_lon_outline),
        "order": list(range(len(queens_lon_outline))),
    }
)

df_boroughs = pd.concat([manhattan_outline, brooklyn_outline, queens_outline], ignore_index=True)

# Title — scale fontsize for length; kept compact so the full string (incl.
# "anyplot.ai") sits inside the panel width and renders at uniform contrast.
title = "NYC Taxi Pickups · hexbin-map-geographic · python · letsplot · anyplot.ai"
title_size = max(12, round(14 * 60 / len(title)))

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
        aes(x=LON, y=LAT, group="borough"),
        data=df_boroughs,
        fill=BASEMAP_FILL,
        color=BASEMAP_COLOR,
        size=0.6,
        alpha=0.7,
    )
    + geom_hex(
        aes(x=LON, y=LAT),
        data=df,
        bins=[N_BINS, N_BINS],
        alpha=0.85,
        tooltips=layer_tooltips().line("Pickups|@..count.."),
    )
    + scale_fill_gradientn(
        colors=[ramp_color(SEQ_FIELDS, k / 255) for k in range(256)], name="Pickup\nCount", trans="log10"
    )
    + labs(x="Longitude (°)", y="Latitude (°)", title=title)
    + coord_fixed(ratio=1.0, xlim=[-74.05, -73.68], ylim=[40.55, 40.90])
    + theme_minimal()
    + anyplot_theme
)

# coord_fixed narrows the plot box; a one-panel grid paints the whole canvas with the page color
plot = gggrid([plot]) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
