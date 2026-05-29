"""anyplot.ai
hexbin-basic: Basic Hexbin Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Created: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    ggplot,
    guide_colorbar,
    labs,
    scale_fill_gradient,
    theme,
    theme_minimal,
)


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

np.random.seed(42)

# Data — seismic epicenters with multi-cluster distribution (Eastern Mediterranean)
lon = np.concatenate(
    [
        np.random.normal(35.5, 0.8, 2500),  # Primary fault zone
        np.random.normal(37.5, 0.5, 1200),  # Aftershock region
        np.random.normal(33.5, 0.4, 600),  # Background cluster
        np.random.uniform(32.0, 39.0, 700),  # Diffuse regional activity
    ]
)
lat = np.concatenate(
    [
        np.random.normal(37.0, 0.7, 2500),
        np.random.normal(38.5, 0.5, 1200),
        np.random.normal(36.5, 0.4, 600),
        np.random.uniform(35.0, 40.0, 700),
    ]
)

# Vectorized hexagonal binning
gridsize = 30
hex_w = (lon.max() - lon.min() + 1.0) / gridsize
hex_h = hex_w * np.sqrt(3) / 2

row_idx = np.round(lat / hex_h).astype(int)
offset = (row_idx % 2) * (hex_w / 2)
col_idx = np.round((lon - offset) / hex_w).astype(int)

bin_df = pd.DataFrame({"cx": np.round(col_idx * hex_w + offset, 6), "cy": np.round(row_idx * hex_h, 6)})
counts = bin_df.groupby(["cx", "cy"]).size().reset_index(name="count")

# Build hex polygon vertices — oversize 1.08 minimises gaps in sparse regions
r = hex_w / np.sqrt(3) * 1.08
angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6
n = len(counts)

hex_df = pd.DataFrame(
    {
        "x": np.repeat(counts["cx"].values, 6) + r * np.cos(np.tile(angles, n)),
        "y": np.repeat(counts["cy"].values, 6) + r * np.sin(np.tile(angles, n)),
        "hex_id": np.repeat(np.arange(n), 6),
        "count": np.repeat(counts["count"].values, 6),
    }
)

title = "Seismic Event Density · hexbin-basic · python · plotnine · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title)))

plot = (
    ggplot(hex_df, aes(x="x", y="y", group="hex_id", fill="count"))
    + geom_polygon(color=PAGE_BG, size=0.15)
    + scale_fill_gradient(low="#009E73", high="#4467A3", name="Event Count", guide=guide_colorbar(nbin=200))
    # Focal annotations identifying the two main seismic clusters
    + annotate("text", x=32.2, y=37.1, label="Primary\nFault Zone →", size=3, color=INK, ha="left")
    + annotate("text", x=38.8, y=38.6, label="← Aftershock\n   Region", size=3, color=INK, ha="right")
    + coord_fixed(ratio=1)
    + labs(x="Longitude (°E)", y="Latitude (°N)", title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=8, color=INK_SOFT),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=title_fontsize, color=INK),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        plot_background=element_rect(fill=PAGE_BG, color="none"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_border=element_rect(color=INK_SOFT, fill=None),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
