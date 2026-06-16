""" anyplot.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-06
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_smooth,
    ggplot,
    ggsave,
    labs,
    theme,
    theme_minimal,
)
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette
BRAND = "#009E73"  # First categorical series
ACCENT = "#C475FD"  # Second series (for regression line)

# Data - Study hours vs exam score relationship
np.random.seed(42)
n_points = 80
study_hours = np.random.uniform(1, 10, n_points)
exam_score = 45 + 5 * study_hours + np.random.normal(0, 6, n_points)
exam_score = np.clip(exam_score, 0, 100)

df = pd.DataFrame({"study_hours": study_hours, "exam_score": exam_score})

# Calculate regression statistics for annotation
slope, intercept, r_value, p_value, std_err = stats.linregress(study_hours, exam_score)
r_squared = r_value**2

# Create regression equation and R² text
equation_text = f"y = {slope:.2f}x + {intercept:.2f}"
r_squared_text = f"R² = {r_squared:.3f}"
annotation_text = f"{equation_text}\n{r_squared_text}"

# Plot
plot = (
    ggplot(df, aes(x="study_hours", y="exam_score"))
    + geom_point(size=4.5, alpha=0.70, color=BRAND)
    + geom_smooth(method="lm", se=True, color=ACCENT, fill=ACCENT, alpha=0.25, size=2)
    + annotate("text", x=2, y=92, label=annotation_text, ha="left", va="top", size=14, color=INK)
    + labs(title="scatter-regression-linear · plotnine · anyplot.ai", x="Study Hours", y="Exam Score (%)")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.08),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.04),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.5),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, color=INK),
        text=element_text(size=14, color=INK),
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", dpi=300, width=16, height=9, verbose=False)
