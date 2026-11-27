"""anyplot.ai
line-impurity-comparison: Gini Impurity vs Entropy Comparison
Library: plotnine 0.15.9 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_linetype_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
P = "Probability (p)"  # role: p
IMPURITY = "Impurity measure (normalized)"  # role: extra
MEASURE = "Splitting criterion"  # role: extra

# Data
p = np.linspace(0, 1, 201)
gini = 2 * p * (1 - p)
entropy = np.where((p > 0) & (p < 1), -p * np.log2(p) - (1 - p) * np.log2(1 - p), 0.0)

GINI_LABEL = "Gini: 2p(1−p)"
ENTROPY_LABEL = "Entropy: −p log₂p − (1−p) log₂(1−p)"

df = pd.DataFrame(
    {
        P: np.tile(p, 2),
        IMPURITY: np.concatenate([gini, entropy]),
        MEASURE: [GINI_LABEL] * len(p) + [ENTROPY_LABEL] * len(p),
    }
)

# Plot
groups = df[MEASURE].unique().tolist()
peaks = df.loc[df.groupby(MEASURE, sort=False)[IMPURITY].idxmax()]
peak_p = peaks[P].iloc[0]
top = df[IMPURITY].max()

# Title with length-scaled fontsize (baseline: 67 chars → 12pt)
title = "line-impurity-comparison · python · plotnine · anyplot.ai"
n = len(title)
title_fontsize = max(8, round(12 * (67 / n if n > 67 else 1.0)))

plot = (
    ggplot(df, aes(x=P, y=IMPURITY, color=MEASURE, linetype=MEASURE))
    + annotate("segment", x=peak_p, xend=peak_p, y=0, yend=top, color=INK_SOFT, size=0.6, linetype="dashed", alpha=0.5)
    + geom_line(size=2.5)
    + geom_point(data=peaks, size=5, show_legend=False)
    + annotate(
        "text",
        x=peak_p,
        y=top * 1.08,
        label=f"Both maxima at p = {peak_p:.1f}",
        size=8,
        ha="center",
        color=INK_SOFT,
        fontstyle="italic",
    )
    + scale_color_manual(values=IMPRINT_PALETTE, limits=groups)
    + scale_linetype_manual(values=["solid", "dashed"], limits=groups)
    + scale_x_continuous(breaks=np.arange(0, 1.1, 0.1))
    + scale_y_continuous(breaks=np.arange(0, 1.1, 0.2))
    + labs(title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        text=element_text(size=7),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=title_fontsize, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK, weight="bold"),
        legend_position="bottom",
        legend_direction="horizontal",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        axis_line=element_line(color=INK_SOFT, size=0.8),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
