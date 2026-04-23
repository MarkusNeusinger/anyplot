""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-23
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = INK
BRAND = "#009E73"

# Data
np.random.seed(42)
n_points = 220
study_hours = np.random.uniform(1, 10, n_points)
exam_scores = np.clip(32 + study_hours * 6 + np.random.randn(n_points) * 7, 15, 100)
df = pd.DataFrame({"study_hours": study_hours, "exam_scores": exam_scores})

# Plot
plot = (
    ggplot(df, aes(x="study_hours", y="exam_scores"))
    + geom_point(shape="o", fill=BRAND, color=PAGE_BG, alpha=0.75, size=4.5, stroke=0.7)
    + scale_x_continuous(breaks=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], expand=(0.02, 0.02))
    + scale_y_continuous(breaks=[20, 30, 40, 50, 60, 70, 80, 90, 100], expand=(0.03, 0.03))
    + coord_cartesian(xlim=(0.5, 10.5), ylim=(15, 100))
    + labs(x="Study Hours (per week)", y="Exam Score (points)", title="scatter-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color=INK_SOFT),
        plot_title=element_text(size=24, color=INK, ha="left", margin={"b": 18}),
        axis_title_x=element_text(size=20, color=INK, margin={"t": 14}),
        axis_title_y=element_text(size=20, color=INK, margin={"r": 14}),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_ticks=element_blank(),
        axis_line_x=element_line(color=INK_SOFT, size=0.6),
        axis_line_y=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=GRID, size=0.4, alpha=0.10),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_margin=0.03,
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
