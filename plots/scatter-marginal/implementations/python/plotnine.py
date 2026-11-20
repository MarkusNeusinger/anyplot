"""anyplot.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: plotnine 0.15.4 | Python 3.13.13
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_histogram,
    geom_point,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from plotnine.composition import plot_spacer


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
SCATTER_COLOR = IMPRINT_PALETTE[0]
MARGINAL_COLOR = IMPRINT_PALETTE[1]

# Columns
STUDY_HOURS = "Study Hours per Week"  # role: x
EXAM_SCORE = "Exam Score (%)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
n = 200
hours = np.clip(rng.normal(25, 8, n), 5, 45)
score = np.clip(35 + 1.5 * hours + rng.normal(0, 8, n), 30, 100)
df = pd.DataFrame({STUDY_HOURS: hours, EXAM_SCORE: score})

# Plot
# Shared axis limits so the marginals align with the scatter
x_lim = (0, df[STUDY_HOURS].max() * 1.12)
y_lim = (df[EXAM_SCORE].min() - 5, df[EXAM_SCORE].max() * 1.05)
title = "scatter-marginal · python · plotnine · anyplot.ai"

# Shared theme - L-shaped spine (left + bottom only)
base_theme = theme_minimal() + theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=element_blank(),
    panel_border=element_blank(),
    axis_title=element_text(color=INK, size=20, weight="bold"),
    axis_text=element_text(color=INK_SOFT, size=16),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    axis_ticks=element_line(color=INK_SOFT, size=0.4),
    plot_title=element_text(color=INK, size=24, weight="bold", margin={"t": 10, "b": 10}),
)

# Top histogram (x distribution)
top_hist = (
    ggplot(df, aes(x=STUDY_HOURS))
    + geom_histogram(bins=15, fill=MARGINAL_COLOR, color=INK_SOFT, alpha=0.7, size=0.3)
    + scale_x_continuous(limits=x_lim)
    + labs(x="", y="", title=title)
    + base_theme
    + theme(
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        axis_ticks_minor_x=element_blank(),
        axis_line_x=element_blank(),
        axis_title_y=element_blank(),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        axis_ticks_minor_y=element_blank(),
        axis_line_y=element_blank(),
        panel_grid_major=element_blank(),
    )
)

# Right histogram (y distribution)
right_hist = (
    ggplot(df, aes(x=EXAM_SCORE))
    + geom_histogram(bins=15, fill=MARGINAL_COLOR, color=INK_SOFT, alpha=0.7, size=0.3)
    + coord_flip()
    + scale_x_continuous(limits=y_lim)
    + labs(x="", y="")
    + base_theme
    + theme(
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        axis_ticks_minor_y=element_blank(),
        axis_line_y=element_blank(),
        axis_title_x=element_blank(),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        axis_ticks_minor_x=element_blank(),
        axis_line_x=element_blank(),
        panel_grid_major=element_blank(),
    )
)

# Main scatter plot
scatter_plot = (
    ggplot(df, aes(x=STUDY_HOURS, y=EXAM_SCORE))
    + geom_point(size=3.5, alpha=0.6, color=SCATTER_COLOR)
    + scale_x_continuous(limits=x_lim)
    + scale_y_continuous(limits=y_lim)
    + labs(x=STUDY_HOURS, y=EXAM_SCORE)
    + base_theme
)

# Spacer
spacer = plot_spacer() + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Compose layout: 16 x 9 in at 200 dpi = 3200 x 1800 px, panels aligned on shared axes
composed = ((top_hist | spacer) / (scatter_plot | right_hist)) & theme(figure_size=(16, 9))

# Save
fig = composed.draw()
fig.savefig(f"plot-{THEME}.png", dpi=200, facecolor=PAGE_BG)
