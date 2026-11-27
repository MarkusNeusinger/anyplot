"""anyplot.ai
density-basic: Basic Density Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-30
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
    geom_area,
    geom_line,
    geom_rug,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint position 1 — always first series

# Columns: set this to your table's column name
SCORE = "Test Score (points)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
scores = np.clip(np.concatenate([np.random.normal(72, 10, 150), np.random.normal(88, 5, 50)]), 0, 100)
df = pd.DataFrame({SCORE: scores})

# Plot
title = "density-basic · python · plotnine · anyplot.ai"
span = df[SCORE].max() - df[SCORE].min()

plot = (
    ggplot(df, aes(x=SCORE))
    + geom_area(aes(y=after_stat("density")), stat="density", fill=BRAND, alpha=0.3, color="none")
    + geom_line(aes(y=after_stat("density")), stat="density", color=BRAND, size=1.8)
    + geom_rug(color=INK_MUTED, alpha=0.5, size=0.6)
    + labs(y="Probability Density", title=title)
    + scale_y_continuous(expand=(0, 0, 0.1, 0))
    + scale_x_continuous(limits=(df[SCORE].min() - 0.25 * span, df[SCORE].max() + 0.25 * span))
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK_SOFT),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        panel_border=element_blank(),
        axis_line=element_line(color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
