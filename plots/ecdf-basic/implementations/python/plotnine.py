""" anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 91/100 | Updated: 2026-04-24
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_step,
    geom_vline,
    ggplot,
    ggsave,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data: test scores — normal distribution centered at 50
np.random.seed(42)
scores = np.random.randn(200) * 15 + 50

# Compute ECDF
sorted_scores = np.sort(scores)
ecdf_y = np.arange(1, len(sorted_scores) + 1) / len(sorted_scores)
median_score = np.median(sorted_scores)

df = pd.DataFrame({"score": sorted_scores, "ecdf": ecdf_y})

# Plot
plot = (
    ggplot(df, aes(x="score", y="ecdf"))
    + geom_hline(yintercept=0.5, color=INK_SOFT, size=0.6, linetype="dotted", alpha=0.7)
    + geom_vline(xintercept=median_score, color=INK_SOFT, size=0.6, linetype="dotted", alpha=0.7)
    + geom_step(color=BRAND, size=2)
    + labs(x="Test Score (points)", y="Cumulative Proportion", title="ecdf-basic · plotnine · anyplot.ai")
    + scale_x_continuous(expand=(0.01, 0))
    + scale_y_continuous(limits=(0, 1), breaks=np.arange(0, 1.1, 0.1), expand=(0.01, 0))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_blank(),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.6),
        axis_ticks=element_line(color=INK_SOFT, size=0.5),
        text=element_text(color=INK, size=14),
        plot_title=element_text(color=INK, size=24, weight="medium", ha="left"),
        axis_title=element_text(color=INK, size=20),
        axis_text=element_text(color=INK_SOFT, size=16),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=16),
        legend_title=element_text(color=INK, size=16),
    )
)

ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9)
