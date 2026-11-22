"""anyplot.ai
line-styled: Styled Line Plot
Library: lets-plot | Python 3.13
Quality: pending | Created: 2025-12-30
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
    geom_line,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    theme,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants: standard line styles in the order the spec lists them (solid, dashed, dotted, dash-dot)
LINE_STYLES = ["solid", "dashed", "dotted", "dotdash", "longdash", "twodash"]

# Columns: set these to your table's column names
DAY = "Day of month"  # role: x
CITIES = ["Paris", "Athens", "Seattle", "Delhi"]  # role: y_

# Data: replace this block with your own table, for example df = pd.read_csv("rainfall.csv")
np.random.seed(42)
n_days = 30
paris = 15 + np.cumsum(np.random.randn(n_days) * 2) / 5
athens = 5 + np.cumsum(np.random.randn(n_days) * 1) / 5
seattle = 20 + np.cumsum(np.random.randn(n_days) * 2.5) / 5
delhi = 8 + np.cumsum(np.random.randn(n_days) * 1.5) / 5
df = pd.DataFrame(
    {DAY: np.arange(1, n_days + 1), CITIES[0]: paris, CITIES[1]: athens, CITIES[2]: seattle, CITIES[3]: delhi}
)

# Plot
RAINFALL = "Rainfall (mm)"
CITY = "City"
long_df = df.melt(id_vars=DAY, value_vars=CITIES, var_name=CITY, value_name=RAINFALL)
n_series = len(CITIES)
title = "line-styled · python · letsplot · anyplot.ai"

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=16, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=10, color=INK),
    legend_position="right",
    legend_key_width=60,
)

plot = (
    ggplot(long_df, aes(x=DAY, y=RAINFALL, color=CITY, linetype=CITY))
    + geom_line(size=1.2)
    + scale_color_manual(values=IMPRINT_PALETTE[:n_series])
    + scale_linetype_manual(values=LINE_STYLES[:n_series])
    + labs(title=title)
    + anyplot_theme
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
