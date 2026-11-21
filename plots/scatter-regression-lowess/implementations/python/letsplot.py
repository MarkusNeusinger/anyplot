"""anyplot.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-14
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_smooth,
    ggplot,
    ggsave,
    ggsize,
    labs,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: points take position 1, the LOWESS curve position 2
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TEMPERATURE = "Temperature (°C)"  # role: x
GROWTH_RATE = "Growth rate (cm/day)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("growth.csv")
np.random.seed(42)
n = 200
temperature = np.linspace(5, 40, n)
growth = (
    15
    + 8 * np.sin((temperature - 5) * np.pi / 35)
    + 3 * np.cos((temperature - 10) * np.pi / 15)
    + np.random.randn(n) * 2.5
)
df = pd.DataFrame({TEMPERATURE: temperature, GROWTH_RATE: growth})

# Plot: reads only df and the constants above
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3),
    panel_grid_minor=element_line(color=INK, size=0.2),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK),
)

plot = (
    ggplot(df, aes(x=TEMPERATURE, y=GROWTH_RATE))
    + geom_point(color=IMPRINT_PALETTE[0], size=2.5, alpha=0.6)
    + geom_smooth(
        method="loess", span=0.4, color=IMPRINT_PALETTE[1], size=1.5, se=True, fill=IMPRINT_PALETTE[1], alpha=0.15
    )
    + labs(title="LOWESS Smoothing · scatter-regression-lowess · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
