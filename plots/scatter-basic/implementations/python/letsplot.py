""" anyplot.ai
scatter-basic: Basic Scatter Plot
Library: letsplot 4.9.0 | Python 3.14.4
Quality: 89/100 | Updated: 2026-04-23
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
    geom_point,
    ggplot,
    ggsize,
    labs,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
# Pre-blended ~10% INK over PAGE_BG (element_line has no alpha)
GRID = "#E4E2DB" if THEME == "light" else "#2F2F2C"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data — study hours vs exam scores (moderate positive correlation)
np.random.seed(42)
study_hours = np.random.uniform(1.0, 10.0, 180)
exam_scores = study_hours * 6.8 + np.random.normal(0, 7.5, 180) + 28
exam_scores = np.clip(exam_scores, 30, 105)
df = pd.DataFrame({"study_hours": study_hours, "exam_scores": exam_scores})

# Plot — shape=21 allows theme-adaptive stroke matching PAGE_BG for marker definition
plot = (
    ggplot(df, aes(x="study_hours", y="exam_scores"))
    + geom_point(shape=21, fill=BRAND, color=PAGE_BG, size=6, alpha=0.75, stroke=0.8)
    + labs(x="Study Hours per Day", y="Exam Score (points)", title="scatter-basic · letsplot · anyplot.ai")
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=GRID, size=0.4),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.4),
        axis_ticks=element_blank(),
        plot_title=element_text(size=24, color=INK, face="bold"),
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
