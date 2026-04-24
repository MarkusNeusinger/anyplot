""" anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: letsplot 4.9.0 | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-24
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
    ggplot,
    ggsize,
    labs,
    scale_y_continuous,
    stat_ecdf,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "#C9C7C1" if THEME == "light" else "#565551"
BRAND = "#009E73"

# Data — Web service response times (ms) with mixed distribution
np.random.seed(42)
response_times = np.concatenate(
    [np.random.exponential(scale=50, size=150), np.random.normal(loc=200, scale=30, size=50)]
)
df = pd.DataFrame({"response_time": response_times})

# Plot — ECDF using stat_ecdf with step geometry
plot = (
    ggplot(df, aes(x="response_time"))
    + stat_ecdf(geom="step", color=BRAND, size=2)
    + labs(
        x="Response Time (ms)",
        y="Cumulative Proportion",
        title="Web Service Response Times · ecdf-basic · letsplot · anyplot.ai",
    )
    + scale_y_continuous(limits=[0, 1], breaks=[0, 0.25, 0.5, 0.75, 1.0])
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=GRID, size=0.6),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.6),
        axis_ticks=element_line(color=INK_SOFT, size=0.5),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_title=element_text(size=20, color=INK),
        plot_title=element_text(size=24, color=INK),
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
