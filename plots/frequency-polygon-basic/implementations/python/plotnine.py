""" anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BINS = 20  # number of shared bins across all groups

# Columns: set these to your table's column names
AGE = "Customer age (years)"  # role: values
SEGMENT = "Segment"  # role: group

# Data: replace this block with your own table, for example df = pd.read_csv("customers.csv")
rng = np.random.default_rng(7)
df = pd.DataFrame(
    {
        AGE: np.concatenate(
            [
                rng.normal(loc=23, scale=3.5, size=300),
                rng.normal(loc=38, scale=8, size=500),
                rng.normal(loc=67, scale=6, size=250),
            ]
        ).clip(18, 90),
        SEGMENT: ["Students"] * 300 + ["Professionals"] * 500 + ["Retirees"] * 250,
    }
)

# Plot: reads only df and the constants above
groups = df[SEGMENT].dropna().unique().tolist()
edges = np.histogram_bin_edges(df[AGE].dropna(), bins=BINS)
step = edges[1] - edges[0]
mids = (edges[:-1] + edges[1:]) / 2
# One vertex per bin midpoint, plus a zero vertex one bin beyond each end to close the polygon
x_vertices = np.concatenate([[mids[0] - step], mids, [mids[-1] + step]])

rows = []
for group in groups:
    counts, _ = np.histogram(df.loc[df[SEGMENT] == group, AGE].dropna(), bins=edges)
    rows.append(pd.DataFrame({AGE: x_vertices, SEGMENT: group, "Frequency": np.concatenate([[0], counts, [0]])}))
poly = pd.concat(rows, ignore_index=True)
poly[SEGMENT] = pd.Categorical(poly[SEGMENT], categories=groups)

anyplot_theme = theme(
    figure_size=(8, 4.5),
    text=element_text(size=7),
    axis_title=element_text(size=10, color=INK),
    axis_text=element_text(size=8, color=INK_SOFT),
    plot_title=element_text(size=12, color=INK),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    axis_line=element_line(color=INK_SOFT, size=0.3),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=8, color=INK_SOFT),
    legend_title=element_text(size=9, color=INK),
    legend_position="right",
)

plot = (
    ggplot(poly, aes(x=AGE, y="Frequency", color=SEGMENT, fill=SEGMENT, group=SEGMENT))
    + geom_area(position="identity", alpha=0.18, size=0)
    + geom_line(size=0.9)
    + geom_point(size=1.6)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=groups)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=groups)
    + scale_y_continuous(limits=(0, None), expand=(0, 0, 0.05, 0))
    + labs(y="Frequency (customers per bin)", title="frequency-polygon-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
