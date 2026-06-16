""" anyplot.ai
histogram-stacked: Stacked Histogram
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-12
"""

import os
import pathlib

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_histogram,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Plant growth measurements across different soil types
np.random.seed(42)

soil_a = np.random.normal(loc=25, scale=5, size=150)
soil_b = np.random.normal(loc=30, scale=6, size=120)
soil_c = np.random.normal(loc=22, scale=4, size=100)

df = pd.DataFrame(
    {
        "height": np.concatenate([soil_a, soil_b, soil_c]),
        "soil_type": (["Sandy Soil"] * 150 + ["Loamy Soil"] * 120 + ["Clay Soil"] * 100),
    }
)

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.4),
    axis_title=element_text(color=INK, size=20),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=24, weight="medium"),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=18),
    legend_position="right",
    figure_size=(16, 9),
)

plot = (
    ggplot(df, aes(x="height", fill="soil_type"))
    + geom_histogram(bins=20, position="stack", alpha=0.85, color=PAGE_BG, size=0.4)
    + labs(x="Plant Height (cm)", y="Frequency", title="histogram-stacked · plotnine · anyplot.ai", fill="Soil Type")
    + scale_fill_manual(values=IMPRINT)
    + theme_minimal()
    + anyplot_theme
)

# Save
plot_dir = pathlib.Path(__file__).parent
plot_dir.mkdir(parents=True, exist_ok=True)
plot.save(str(plot_dir / f"plot-{THEME}.png"), dpi=300)
