"""anyplot.ai
hexbin-basic: Basic Hexbin Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Created: 2026-05-29
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_polygon,
    ggplot,
    guide_colorbar,
    labs,
    scale_fill_gradientn,
    theme,
    theme_minimal,
)


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential ramp for filled cells (single polarity), stops per theme
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants
GRIDSIZE = 30  # hexagons across the longitude range
HEX_OVERSIZE = 1.08  # hexagons drawn slightly larger than their cell so no gaps show

# Columns: set these to your table's column names
LONGITUDE = "Longitude (°E)"  # role: x
LATITUDE = "Latitude (°N)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("events.csv")
# Seismic epicenters with a multi-cluster distribution (Eastern Mediterranean)
rng = np.random.default_rng(42)
df = pd.DataFrame(
    {
        LONGITUDE: np.concatenate(
            [
                rng.normal(35.5, 0.8, 2500),  # Primary fault zone
                rng.normal(37.5, 0.5, 1200),  # Aftershock region
                rng.normal(33.5, 0.4, 600),  # Background cluster
                rng.uniform(32.0, 39.0, 700),  # Diffuse regional activity
            ]
        ),
        LATITUDE: np.concatenate(
            [
                rng.normal(37.0, 0.7, 2500),
                rng.normal(38.5, 0.5, 1200),
                rng.normal(36.5, 0.4, 600),
                rng.uniform(35.0, 40.0, 700),
            ]
        ),
    }
)

# Plot: reads only df and the constants above
# plotnine has no hexbin geom, so points are binned into a hexagonal grid and drawn as polygons
points = df[[LONGITUDE, LATITUDE]].dropna()
lon = points[LONGITUDE].to_numpy()
lat = points[LATITUDE].to_numpy()

hex_w = (lon.max() - lon.min()) / GRIDSIZE
hex_h = hex_w * np.sqrt(3) / 2

row_idx = np.round(lat / hex_h).astype(int)
offset = (row_idx % 2) * (hex_w / 2)
col_idx = np.round((lon - offset) / hex_w).astype(int)

bin_df = pd.DataFrame({"cx": np.round(col_idx * hex_w + offset, 6), "cy": np.round(row_idx * hex_h, 6)})
counts = bin_df.groupby(["cx", "cy"]).size().reset_index(name="count")

r = hex_w / np.sqrt(3) * HEX_OVERSIZE
angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6
n = len(counts)

hex_df = pd.DataFrame(
    {
        "x": np.repeat(counts["cx"].to_numpy(), 6) + r * np.cos(np.tile(angles, n)),
        "y": np.repeat(counts["cy"].to_numpy(), 6) + r * np.sin(np.tile(angles, n)),
        "hex_id": np.repeat(np.arange(n), 6),
        "count": np.repeat(counts["count"].to_numpy(), 6),
    }
)

title = "Seismic Event Density · hexbin-basic · python · plotnine · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title)))

plot = (
    ggplot(hex_df, aes(x="x", y="y", group="hex_id", fill="count"))
    + geom_polygon(color=PAGE_BG, size=0.15)
    + scale_fill_gradientn(
        colors=[c for _, c in SEQ_FIELDS],
        values=[p for p, _ in SEQ_FIELDS],
        name="Event count",
        guide=guide_colorbar(nbin=200),
    )
    + coord_fixed(ratio=1)
    + labs(x=LONGITUDE, y=LATITUDE, title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=8, color=INK_SOFT),
        axis_title=element_text(size=11, color=INK),
        axis_text=element_text(size=9, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=title_fontsize, color=INK),
        legend_title=element_text(size=10, color=INK),
        legend_text=element_text(size=9, color=INK_SOFT),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        plot_background=element_rect(fill=PAGE_BG, color="none"),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
