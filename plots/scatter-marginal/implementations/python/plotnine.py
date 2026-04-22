""" pyplots.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

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


# Data - Bivariate data with moderate correlation (realistic scenario)
np.random.seed(42)
n = 200

# Study hours vs exam score with positive correlation
study_hours = np.random.normal(25, 8, n)
study_hours = np.clip(study_hours, 5, 45)  # Realistic range
noise = np.random.normal(0, 8, n)
exam_score = 35 + 1.5 * study_hours + noise
exam_score = np.clip(exam_score, 30, 100)

df = pd.DataFrame({"study_hours": study_hours, "exam_score": exam_score})

# Shared axis limits (include all data with margin)
x_min, x_max = 0, 50
y_min, y_max = 30, 105

# Figure sizes calculated for 4800x2700 final output at 300 DPI
# Total: 16x9 inches = 4800x2700 px
# Layout: scatter (12x6.5), top hist (12x2.5), right hist (4x6.5), spacer (4x2.5)
main_w, main_h = 12, 6.5
marg_w, marg_h = 4, 2.5

# Common theme elements for large canvas
base_theme = theme_minimal() + theme(
    text=element_text(size=14),
    axis_title=element_text(size=20),
    axis_text=element_text(size=16),
    plot_title=element_text(size=24),
    panel_grid_major=element_line(color="#cccccc", size=0.5, alpha=0.3),
    panel_grid_minor=element_blank(),
    plot_background=element_rect(fill="white"),
)

# Top histogram (x distribution)
top_hist = (
    ggplot(df, aes(x="study_hours"))
    + geom_histogram(bins=15, fill="#306998", color="#1a3d5c", alpha=0.7, size=0.3)
    + scale_x_continuous(limits=(x_min, x_max))
    + labs(x="", y="", title="scatter-marginal · plotnine · pyplots.ai")
    + base_theme
    + theme(
        figure_size=(main_w, marg_h),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        axis_title_y=element_blank(),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
    )
)

# Right histogram (y distribution, flipped)
right_hist = (
    ggplot(df, aes(x="exam_score"))
    + geom_histogram(bins=15, fill="#FFD43B", color="#d4a80a", alpha=0.7, size=0.3)
    + coord_flip()
    + scale_x_continuous(limits=(y_min, y_max))
    + labs(x="", y="")
    + base_theme
    + theme(
        figure_size=(marg_w, main_h),
        axis_text_y=element_blank(),
        axis_ticks_major_y=element_blank(),
        axis_title_x=element_blank(),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
    )
)

# Main scatter plot
scatter_plot = (
    ggplot(df, aes(x="study_hours", y="exam_score"))
    + geom_point(size=3.5, alpha=0.6, color="#306998")
    + scale_x_continuous(limits=(x_min, x_max))
    + scale_y_continuous(limits=(y_min, y_max))
    + labs(x="Study Hours per Week", y="Exam Score (%)")
    + base_theme
    + theme(figure_size=(main_w, main_h))
)

# Empty spacer for top-right corner
spacer = plot_spacer() + theme(figure_size=(marg_w, marg_h))

# Compose: top row (histogram | spacer), bottom row (scatter | right histogram)
top_row = top_hist | spacer
bottom_row = scatter_plot | right_hist
composed = top_row / bottom_row

# Draw to matplotlib figure and save with correct dimensions
fig = composed.draw()
fig.set_size_inches(16, 9)
fig.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
