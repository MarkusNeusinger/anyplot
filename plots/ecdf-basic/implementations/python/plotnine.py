"""anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 91/100 | Updated: 2026-06-25
"""

import os
import sys

import numpy as np
import pandas as pd


# Avoid shadowing the plotnine library when this file is run directly
_cwd = os.getcwd()
sys.path = [p for p in sys.path if os.path.abspath(p) != _cwd]

from plotnine import (  # noqa: E402
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_vline,
    ggplot,
    ggsave,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    stat_ecdf,
    theme,
    theme_minimal,
)


# Theme tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Imprint palette position 1

# Data: test scores — normal distribution
np.random.seed(42)
scores = np.random.randn(200) * 15 + 50
median_score = float(np.median(scores))

df = pd.DataFrame({"score": scores})

title = "ecdf-basic · python · plotnine · anyplot.ai"

# Plot — stat_ecdf computes ECDF internally via plotnine's stat layer
plot = (
    ggplot(df, aes(x="score"))
    + geom_hline(yintercept=0.5, color=INK_SOFT, size=0.6, linetype="dotted", alpha=0.7)
    + geom_vline(xintercept=median_score, color=INK_SOFT, size=0.6, linetype="dotted", alpha=0.7)
    + stat_ecdf(geom="step", color=BRAND, size=1.0)
    + annotate(
        "text", x=median_score + 2, y=0.08, label=f"Median: {median_score:.1f}", color=INK_MUTED, size=3.5, ha="left"
    )
    + labs(x="Test Score (points)", y="Cumulative Proportion", title=title)
    + scale_x_continuous(expand=(0.01, 0))
    + scale_y_continuous(limits=(0, 1), breaks=np.arange(0, 1.1, 0.1), expand=(0.01, 0))
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_border=element_blank(),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.15),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.6),
        axis_ticks=element_line(color=INK_SOFT, size=0.5),
        text=element_text(color=INK, size=7),
        plot_title=element_text(color=INK, size=12, weight="medium", ha="left"),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=8),
        legend_title=element_text(color=INK, size=8),
    )
)

ggsave(plot, filename=f"plot-{THEME}.png", dpi=400, width=8, height=4.5)
