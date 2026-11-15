"""anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-08
"""

import os

import numpy as np
import pandas as pd
from plotnine import aes, element_line, element_rect, element_text, geom_bin2d, ggplot, labs, scale_fill_gradient, theme


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: sequential ramp for the bin counts (single polarity)
IMPRINT_SEQ = ("#009E73", "#4467A3")

# Constants
BINS = 28  # bins per axis

# Columns: set these to your table's column names
ASSET_RETURNS = "Asset returns (%)"  # role: x
INDEX_RETURNS = "Index returns (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("returns.csv")
# Context: financial returns across asset classes, bivariate normal with correlation
rng = np.random.default_rng(42)
xy = rng.multivariate_normal([5.2, 8.1], [[2.5, 1.8], [1.8, 4.2]], 5000)
df = pd.DataFrame({ASSET_RETURNS: xy[:, 0], INDEX_RETURNS: xy[:, 1]})

# Plot: reads only df and the constants above
title = "histogram-2d · python · plotnine · anyplot.ai"
plot = (
    ggplot(df, aes(x=ASSET_RETURNS, y=INDEX_RETURNS))
    + geom_bin2d(bins=BINS)
    + scale_fill_gradient(low=IMPRINT_SEQ[0], high=IMPRINT_SEQ[1], name="Count")
    + labs(title=title)
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        panel_grid_major=element_line(color=INK, size=0.2, alpha=0.1),
        panel_grid_minor=element_line(color=INK, size=0.1, alpha=0.05),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        plot_title=element_text(size=12, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=10, color=INK),
        text=element_text(size=7),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
