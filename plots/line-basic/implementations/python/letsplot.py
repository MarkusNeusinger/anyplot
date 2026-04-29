""" anyplot.ai
line-basic: Basic Line Plot
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-04-29
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
    geom_point,
    ggplot,
    ggsize,
    labs,
    scale_x_continuous,
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
RULE = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"
BRAND = "#009E73"

# Data - Monthly temperature readings over a year
np.random.seed(42)
months = np.arange(1, 13)
base_temp = 15 + 12 * np.sin((months - 4) * np.pi / 6)
temperature = base_temp + np.random.randn(12) * 1.5

df = pd.DataFrame({"month": months, "temperature": temperature})

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=RULE, size=0.5),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24),
)

plot = (
    ggplot(df, aes(x="month", y="temperature"))
    + geom_line(color=BRAND, size=2)
    + geom_point(color=BRAND, size=5, alpha=0.9)
    + labs(x="Month", y="Temperature (°C)", title="line-basic · letsplot · anyplot.ai")
    + scale_x_continuous(breaks=list(range(1, 13)))
    + ggsize(1600, 900)
    + theme_minimal()
    + anyplot_theme
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
