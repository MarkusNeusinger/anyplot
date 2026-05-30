"""anyplot.ai
density-basic: Basic Density Plot
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-05-30
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
    geom_density,
    geom_segment,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — always first series

# Data - Marathon finish times: trimodal distribution with realistic right skew
np.random.seed(42)
finish_minutes = np.concatenate(
    [
        np.random.normal(240, 25, 350),  # Main pack (~4 hour runners)
        np.random.normal(200, 15, 100),  # Competitive runners (~3:20)
        np.random.normal(300, 20, 50),  # Casual runners (~5 hours)
    ]
)
finish_minutes = np.clip(finish_minutes, 140, 400)
df = pd.DataFrame({"time": finish_minutes})

# Rug data: individual observations as small vertical ticks at the x-axis
rug_df = pd.DataFrame({"x": finish_minutes, "y0": 0.0, "y1": 0.0003})

# Title
title = "density-basic · python · letsplot · anyplot.ai"

# Chrome theme (theme-adaptive background, text, grid)
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_blank(),
    panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_ticks=element_blank(),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
)

# Plot
plot = (
    ggplot(df, aes(x="time"))
    + geom_density(
        fill=BRAND,
        color=BRAND,
        alpha=0.35,
        size=1.5,
        kernel="gaussian",
        adjust=0.85,
        trim=True,
        tooltips=layer_tooltips().line("density|@..density.."),
    )
    + geom_segment(data=rug_df, mapping=aes(x="x", y="y0", xend="x", yend="y1"), color=BRAND, alpha=0.30, size=0.4)
    + labs(x="Finish Time (minutes)", y="Density (×10⁻³)", title=title)
    + scale_x_continuous(breaks=list(range(150, 401, 50)))
    + scale_y_continuous(
        breaks=[0.002, 0.004, 0.006, 0.008, 0.010], labels=["2", "4", "6", "8", "10"], expand=[0.02, 0, 0.15, 0]
    )
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save — theme-suffixed filenames, scale=4 → 3200×1800 px
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
