""" anyplot.ai
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

# Okabe-Ito palette
BRAND = "#009E73"  # Position 1 - for scatter points
ACCENT = "#C475FD"  # Position 2 - for LOWESS curve

# Data - Complex non-linear relationship (plant growth vs temperature)
np.random.seed(42)
n = 200
x = np.linspace(5, 40, n)
y = 15 + 8 * np.sin((x - 5) * np.pi / 35) + 3 * np.cos((x - 10) * np.pi / 15) + np.random.randn(n) * 2.5
df = pd.DataFrame({"temperature": x, "growth_rate": y})

# Theme-adaptive styling
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3),
    panel_grid_minor=element_line(color=INK, size=0.2),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK),
)

# Plot
plot = (
    ggplot(df, aes(x="temperature", y="growth_rate"))
    + geom_point(color=BRAND, size=4, alpha=0.6)
    + geom_smooth(method="loess", span=0.4, color=ACCENT, size=2.5, se=True, fill=ACCENT, alpha=0.15)
    + labs(x="Temperature (°C)", y="Growth Rate (cm/day)", title="scatter-regression-lowess · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
