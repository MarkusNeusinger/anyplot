"""anyplot.ai
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

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BINS = 20

# Columns
HEIGHT = "Plant Height (cm)"  # role: values
SOIL = "Soil Type"  # role: group

# Data - Plant growth measurements across different soil types (Imprint palette)
np.random.seed(42)
sizes = {"Sandy Soil": 150, "Loamy Soil": 120, "Clay Soil": 100}
centers = {"Sandy Soil": (25, 5), "Loamy Soil": (30, 6), "Clay Soil": (22, 4)}
df = pd.DataFrame(
    {
        HEIGHT: np.concatenate([np.random.normal(*centers[g], size=n) for g, n in sizes.items()]),
        SOIL: np.repeat(list(sizes), list(sizes.values())),
    }
)

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None, size=0.4),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=10),
    legend_position="right",
    figure_size=(8, 4.5),
)

plot = (
    ggplot(df, aes(x=HEIGHT, fill=SOIL))
    + geom_histogram(bins=BINS, position="stack", alpha=0.85, color=PAGE_BG, size=0.4)
    + labs(y="Frequency", title="histogram-stacked · python · plotnine · anyplot.ai")
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=df[SOIL].unique().tolist())
    + theme_minimal()
    + anyplot_theme
)

# Save
plot_dir = pathlib.Path(__file__).parent
plot.save(str(plot_dir / f"plot-{THEME}.png"), dpi=400, width=8, height=4.5, units="in")
