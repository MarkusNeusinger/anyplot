""" anyplot.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 87/100 | Updated: 2026-08-05
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
BRAND = "#009E73"  # Imprint position 1 — scatter points
ACCENT = "#C475FD"  # Imprint position 2 — regression line + CI band

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

equation_text = f"y = {slope:.2f}x + {intercept:.2f}"
r_squared_text = f"R² = {r_squared:.3f}"
annotation_text = f"{equation_text}\n{r_squared_text}"

# Title — mandated format, length within the 67-char baseline so fontsize stays at default
title = "scatter-regression-linear · python · plotnine · anyplot.ai"
title_fontsize = round(12 * (67 / len(title) if len(title) > 67 else 1.0))

# Plot
plot = (
    ggplot(df, aes(x="study_hours", y="exam_score"))
    + geom_point(size=3.0, alpha=0.70, color=BRAND)
    + geom_smooth(method="lm", se=True, color=ACCENT, fill=ACCENT, alpha=0.25, size=1.2)
    + annotate("text", x=2, y=92, label=annotation_text, ha="left", va="top", size=3.5, color=INK)
    + labs(title=title, x="Study Hours", y="Exam Score (%)")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.08),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.04),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=title_fontsize, color=INK),
        text=element_text(size=7, color=INK),
    )
)

# Save
ggsave(plot, filename=f"plot-{THEME}.png", dpi=400, width=8, height=4.5, verbose=False)
