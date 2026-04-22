""" pyplots.ai
hexbin-basic: Basic Hexbin Plot
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-21
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    ggplot,
    guide_colorbar,
    labs,
    scale_fill_cmap,
    theme,
    theme_minimal,
)


np.random.seed(42)

# Data — Seismic sensor readings with clustered epicenters
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

# Build hex polygon vertices (fully vectorized)
# Slight oversize (1.02x) ensures tight tiling with no gaps between hexagons
r = hex_w / np.sqrt(3) * 1.02
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

bg = "#f0edeb"

plot = (
    ggplot(hex_df, aes(x="x", y="y", group="hex_id", fill="count"))
    + geom_polygon(color=bg, size=0.15)
    + scale_fill_cmap("inferno", name="Event Count", guide=guide_colorbar(nbin=200))
    + coord_fixed(ratio=1)
    + labs(x="Longitude (°E)", y="Latitude (°N)", title="Seismic Event Density · hexbin-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#2a2035"),
        axis_title=element_text(size=20, weight="bold"),
        axis_text=element_text(size=16, color="#4a4458"),
        plot_title=element_text(size=24, weight="bold", color="#1a1423"),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=bg, color="none"),
        plot_background=element_rect(fill=bg, color="none"),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
