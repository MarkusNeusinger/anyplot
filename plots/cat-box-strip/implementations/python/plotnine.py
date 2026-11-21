""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
"""

import os
import sys


# Remove current directory from path to avoid shadowing plotnine library
if sys.path and sys.path[0]:
    sys.path.pop(0)

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_boxplot,
    geom_jitter,
    ggplot,
    labs,
    position_jitter,
    scale_color_manual,
    scale_fill_manual,
    scale_x_discrete,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
FERTILIZER = "Treatment Group"  # role: category
GROWTH = "Plant Growth (cm)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("growth.csv")
np.random.seed(42)
n_per_group = 40
control = np.random.normal(loc=25, scale=5, size=n_per_group)
fert_a = np.random.normal(loc=35, scale=6, size=n_per_group)
fert_b = np.random.normal(loc=42, scale=4, size=n_per_group)
# Fertilizer C: best results, with a small low-yield subgroup
fert_c = np.concatenate(
    [np.random.normal(loc=48, scale=4, size=n_per_group - 5), np.random.normal(loc=30, scale=3, size=5)]
)
df = pd.DataFrame(
    {
        FERTILIZER: np.repeat(["Control", "Fertilizer A", "Fertilizer B", "Fertilizer C"], n_per_group),
        GROWTH: np.concatenate([control, fert_a, fert_b, fert_c]),
    }
)

# Plot
groups = df[FERTILIZER].unique().tolist()
plot = (
    ggplot(df, aes(x=FERTILIZER, y=GROWTH, fill=FERTILIZER))
    + geom_boxplot(alpha=0.7, width=0.6, outlier_shape="", size=0.6, color=INK_SOFT)
    + geom_jitter(
        aes(color=FERTILIZER),
        position=position_jitter(width=0.15, height=0, random_state=42),
        alpha=0.6,
        size=1.8,
        show_legend=False,
    )
    + scale_x_discrete(limits=groups)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=groups)
    + scale_color_manual(values=IMPRINT_PALETTE, limits=groups)
    + labs(title="cat-box-strip · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        text=element_text(size=7),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_position="right",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
