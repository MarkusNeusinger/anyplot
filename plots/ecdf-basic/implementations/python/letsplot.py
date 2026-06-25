"""anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: letsplot | Python 3.14
Quality: pending | Created: 2026-06-25
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
    layer_tooltips,
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
# Imprint palette — grid at ~15% opacity, pre-blended with PAGE_BG
GRID = "#D8D7D0" if THEME == "light" else "#3A3A36"
BRAND = "#009E73"

# Data — web service response times (ms) with bimodal distribution
np.random.seed(42)
response_times = np.concatenate(
    [np.random.exponential(scale=50, size=150), np.random.normal(loc=200, scale=30, size=50)]
)
df = pd.DataFrame({"response_time": response_times})

# Title — 3-part format, 44 chars (< 67 baseline, no scaling needed)
title = "ecdf-basic · python · letsplot · anyplot.ai"

# Plot — ECDF step function with interactive tooltips (lets-plot HTML capability)
plot = (
    ggplot(df, aes(x="response_time"))
    + stat_ecdf(
        geom="step", color=BRAND, size=1.5, tooltips=layer_tooltips().line("Response Time: @response_time{,.0f} ms")
    )
    + labs(x="Response Time (ms)", y="Cumulative Proportion", title=title)
    + scale_y_continuous(limits=[0, 1], breaks=[0, 0.25, 0.5, 0.75, 1.0])
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major=element_line(color=GRID, size=0.5),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.6),
        axis_ticks=element_line(color=INK_SOFT, size=0.5),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        plot_title=element_text(size=16, color=INK),
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
