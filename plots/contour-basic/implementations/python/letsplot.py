"""anyplot.ai
contour-basic: Basic Contour Plot
Library: letsplot | Python 3.13
Quality: pending | Updated: 2026-06-25
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_contour,
    geom_contourf,
    ggplot,
    ggsize,
    labs,
    scale_fill_gradient2,
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
RULE = "#D6D3C7" if THEME == "light" else "#3A3A34"

# Imprint diverging midpoint — theme-adaptive near-neutral (zero-crossing blends to bg)
MID = PAGE_BG

# Data — 2D Gaussian surface with two peaks and a depression
np.random.seed(42)
n_points = 80
x = np.linspace(-3, 3, n_points)
y = np.linspace(-3, 3, n_points)
X, Y = np.meshgrid(x, y)

Z = (
    np.exp(-((X - 1) ** 2 + (Y - 1) ** 2))
    + 0.7 * np.exp(-((X + 1) ** 2 + (Y + 1) ** 2))
    - 0.3 * np.exp(-(X**2 + (Y - 1.5) ** 2) / 0.5)
)

df = pd.DataFrame({"x": X.flatten(), "y": Y.flatten(), "z": Z.flatten()})

# Title: 46 chars < 67 baseline → no shrink needed; size stays at 16
title = "contour-basic · python · letsplot · anyplot.ai"
title_size = 16

plot = (
    ggplot(df, aes(x="x", y="y", z="z"))
    + geom_contourf(aes(fill="..level.."), bins=12)
    + geom_contour(color=INK, size=0.4, alpha=0.4, bins=12)
    + scale_fill_gradient2(low="#AE3030", mid=MID, high="#4467A3", midpoint=0, name="Surface Height")
    + labs(x="X Coordinate", y="Y Coordinate", title=title)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=RULE, size=0.3),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        axis_ticks=element_line(color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        plot_title=element_text(size=title_size, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
