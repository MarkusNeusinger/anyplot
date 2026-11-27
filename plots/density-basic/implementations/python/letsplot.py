"""anyplot.ai
density-basic: Basic Density Plot
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-05-30
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
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave
from scipy.stats import gaussian_kde


LetsPlot.setup_html()

# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"  # Imprint palette position 1 — always first series

title = "density-basic · python · letsplot · anyplot.ai"

# Constants
RUG_HEIGHT = 0.0003  # rug tick height in density units

# Chrome theme (theme-adaptive background, text, grid)
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_blank(),
    axis_line=element_blank(),
    panel_grid_major_x=element_blank(),
    panel_grid_major_y=element_line(color=GRID, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_ticks=element_blank(),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
)

# Columns
FINISH_TIME = "Finish Time (minutes)"  # role: values

# Data
# Marathon finish times: trimodal distribution with realistic right skew
np.random.seed(42)
finish_minutes = np.concatenate(
    [
        np.random.normal(240, 25, 350),  # Main pack (~4 hour runners)
        np.random.normal(200, 15, 100),  # Competitive runners (~3:20)
        np.random.normal(300, 20, 50),  # Casual runners (~5 hours)
    ]
)
finish_minutes = np.clip(finish_minutes, 140, 400)
df = pd.DataFrame({FINISH_TIME: finish_minutes})

# Plot
# Peak of the same Gaussian KDE (adjust 0.85), used to leave headroom above the curve
values = df[FINISH_TIME].dropna()
kde = gaussian_kde(values, bw_method=lambda k: 0.85 * k.scotts_factor())
density_peak = kde(np.linspace(values.min(), values.max(), 400)).max()

plot = (
    ggplot(df, aes(x=FINISH_TIME))
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
    + geom_segment(aes(xend=FINISH_TIME), y=0, yend=RUG_HEIGHT, color=BRAND, alpha=0.40, size=0.6)
    + labs(y="Density", title=title)
    + scale_y_continuous(expand=[0.0, 0.0], limits=[0, density_peak * 1.15])
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save — theme-suffixed filenames, scale=4 → 3200×1800 px
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
