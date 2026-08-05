"""anyplot.ai
histogram-kde: Histogram with KDE Overlay
Library: plotnine 0.15.7 | Python 3.13.13
Quality: 90/100 | Updated: 2026-08-05
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    element_line,
    element_rect,
    element_text,
    geom_density,
    geom_histogram,
    geom_vline,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


# Theme tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Stock daily returns (realistic financial data)
np.random.seed(42)
# Simulate stock returns with slight negative skew and fat tails (realistic market behavior)
returns = np.concatenate(
    [
        np.random.normal(0.001, 0.015, 400),  # Normal trading days
        np.random.normal(-0.02, 0.03, 80),  # Volatile periods
        np.random.normal(0.005, 0.008, 120),  # Low volatility periods
    ]
)
returns = returns * 100  # Convert to percentage

df = pd.DataFrame({"returns": returns})
mean_return = returns.mean()

# Plot - Histogram with KDE overlay, mean marked for distributional context
plot = (
    ggplot(df, aes(x="returns"))
    + geom_histogram(aes(y=after_stat("density")), bins=35, fill=BRAND, color=BRAND, alpha=0.5, size=0.2)
    + geom_density(color=INK, size=1.1)
    + geom_vline(xintercept=mean_return, color=INK_SOFT, linetype="dashed", size=0.6)
    + labs(x="Daily Return (%)", y="Density", title="histogram-kde · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.3),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.3),
        plot_title=element_text(size=12, color=INK),
        text=element_text(size=7),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
