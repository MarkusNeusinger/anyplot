"""anyplot.ai
hexbin-basic: Basic Hexbin Plot
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

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


LetsPlot.setup_html()

# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential ramp for filled cells (position, hex), per theme
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Constants
HEX_BINS = 35  # hexagons across each axis

# Columns: set these to your table's column names
EAST_KM = "East–West (km from center)"  # role: x
NORTH_KM = "North–South (km from center)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("pings.csv")
# Simulated GPS ping density across a metro area (km from city center)
np.random.seed(42)
n_points = 10000

# Downtown core - elongated east-west along commercial corridor
downtown_east = np.random.randn(n_points // 2) * 2.0 + 4
downtown_north = np.random.randn(n_points // 2) * 1.2 + 3

# University campus - compact circular footprint
campus_east = np.random.randn(n_points // 3) * 1.0 - 3
campus_north = np.random.randn(n_points // 3) * 1.0 + 1

# Transit hub - tight cluster of commuters
transit_east = np.random.randn(n_points // 6) * 0.5 + 0.5
transit_north = np.random.randn(n_points // 6) * 0.5 - 3.5

# Sparse residential pings across outer metro area
bg_east = np.random.uniform(-7, 9, n_points // 10)
bg_north = np.random.uniform(-6, 7, n_points // 10)

df = pd.DataFrame(
    {
        EAST_KM: np.concatenate([downtown_east, campus_east, transit_east, bg_east]),
        NORTH_KM: np.concatenate([downtown_north, campus_north, transit_north, bg_north]),
    }
)

# Plot - Hexagonal binning to reveal density hotspots
plot = (
    ggplot(df, aes(x=EAST_KM, y=NORTH_KM))
    + geom_hex(
        aes(fill="..count.."),
        bins=[HEX_BINS, HEX_BINS],
        color=PAGE_BG,
        size=0.3,
        tooltips=layer_tooltips()
        .title("Hex Bin")
        .line("pings|@..count..")
        .line("density|@..density..")
        .format("@..density..", ".3f"),
    )
    + scale_fill_gradientn(
        colors=[ramp_color(SEQ_FIELDS, k / 255) for k in range(256)], name="Ping Count", trans="sqrt"
    )
    + coord_fixed()
    + labs(
        title="hexbin-basic · python · letsplot · anyplot.ai",
        subtitle="GPS ping density — sqrt-scaled Imprint sequential colormap",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_subtitle=element_text(size=11, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, face="bold", color=INK),
    )
)

# The fixed aspect narrows the plot box; a one-panel grid paints the full canvas with the page color
plot = gggrid([plot]) + ggsize(800, 450) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save PNG (scale=4 gives 3200×1800)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)

# Save HTML for interactive tooltips
ggsave(plot, f"plot-{THEME}.html", path=".")
