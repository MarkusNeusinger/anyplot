""" anyplot.ai
histogram-density: Density Histogram
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-11
"""

import os
import sys

import numpy as np
import pandas as pd


# noqa: E402 - path manipulation needed before plotnine import to avoid namespace conflict
for path in list(sys.path):
    if path.endswith("histogram-density/implementations/python"):
        sys.path.remove(path)

from plotnine import (  # noqa: E402
    aes,
    after_stat,
    element_line,
    element_rect,
    element_text,
    geom_density,
    geom_histogram,
    ggplot,
    labs,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2

# Data - bimodal distribution for compelling visualization
np.random.seed(42)
n_samples = 500

group1 = np.random.normal(loc=65, scale=8, size=n_samples // 2)
group2 = np.random.normal(loc=85, scale=6, size=n_samples // 2)
values = np.concatenate([group1, group2])

df = pd.DataFrame({"values": values})

# Theme configuration
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=16),
    figure_size=(16, 9),
)

# Plot
plot = (
    ggplot(df, aes(x="values"))
    + geom_histogram(aes(y=after_stat("density")), bins=30, fill=BRAND, color="white", alpha=0.7)
    + geom_density(color=ACCENT, size=2, alpha=0.8)
    + labs(x="Test Score (points)", y="Density", title="histogram-density · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
