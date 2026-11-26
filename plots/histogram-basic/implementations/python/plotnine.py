""" anyplot.ai
histogram-basic: Basic Histogram
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-26
"""

import os
import sys


# Remove this file's directory from sys.path to prevent self-import
# (this file is named plotnine.py, same as the library being imported)
_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _dir]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_histogram,
    ggplot,
    labs,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: first series is always brand green
BRAND = "#009E73"
EDGE = "#006B4F"

# Columns: set these to your table's column names
SCORE = "Test Score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
group_a = rng.normal(loc=45, scale=10, size=275)
group_b = rng.normal(loc=80, scale=7, size=225)
df = pd.DataFrame({SCORE: np.clip(np.concatenate([group_a, group_b]), 0, 100)})

# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=SCORE))
    + geom_histogram(bins=30, fill=BRAND, color=EDGE, size=0.3)
    + scale_y_continuous(expand=(0, 0, 0.05, 0))
    + labs(y="Frequency (count)", title="histogram-basic · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK_SOFT),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK, weight="bold"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        panel_border=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        axis_line=element_line(color=INK_SOFT),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
