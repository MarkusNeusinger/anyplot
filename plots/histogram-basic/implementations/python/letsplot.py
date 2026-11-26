"""anyplot.ai
histogram-basic: Basic Histogram
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-28
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
    geom_histogram,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette position 1
BRAND = "#009E73"

# Constants
N_BINS = 30

# Columns
DIAMETER = "Trunk diameter (cm)"  # role: values

# Data: trunk diameters of one cherry cultivar (Kwanzan), right-skewed with a tail of large specimens
rng = np.random.default_rng(42)
main_cluster = rng.normal(37.0, 4.0, 220)
large_specimens = rng.uniform(48.0, 58.0, 30)
df = pd.DataFrame({DIAMETER: np.concatenate([main_cluster, large_specimens])})

# Plot
title = "histogram-basic · python · letsplot · anyplot.ai"

plot = (
    ggplot(df, aes(x=DIAMETER))
    + geom_histogram(
        bins=N_BINS,
        fill=BRAND,
        alpha=0.9,
        size=0.3,
        color=PAGE_BG,
        tooltips=layer_tooltips().format("..count..", "d").format("^x", ".1f").line("Count|@..count.."),
    )
    + scale_y_continuous(name="Frequency", format="d")
    + labs(title=title)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=GRID, size=0.5),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
