"""anyplot.ai
histogram-density: Density Histogram
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-11
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_density,
    geom_histogram,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: bars take position 1, the density curve position 2
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SCORE = "Test score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
df = pd.DataFrame({SCORE: np.concatenate([np.random.normal(65, 8, 250), np.random.normal(85, 6, 250)])})

# Plot: reads only df and the constants above
CURVE = "Series"
curve_df = df.copy()
curve_df[CURVE] = "Kernel density estimate"

anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_x=element_blank(),
    panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=element_rect(color=INK_SOFT, fill=None),
    axis_title=element_text(color=INK, size=10),
    axis_text=element_text(color=INK_SOFT, size=8),
    axis_line=element_line(color=INK_SOFT),
    plot_title=element_text(color=INK, size=12),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
    legend_text=element_text(color=INK_SOFT, size=8),
    legend_title=element_text(color=INK, size=8),
    legend_position=(0.97, 0.95),
    legend_direction="vertical",
)

plot = (
    ggplot(df, aes(x=SCORE))
    + geom_histogram(aes(y=after_stat("density")), bins=30, fill=IMPRINT_PALETTE[0], color=PAGE_BG, alpha=0.8)
    + geom_density(aes(x=SCORE, color=CURVE), data=curve_df, size=1.2)
    + scale_color_manual(values=[IMPRINT_PALETTE[1]])
    + labs(y="Density", color="", title="histogram-density · python · plotnine · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
