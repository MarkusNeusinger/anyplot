""" pyplots.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_text,
    geom_point,
    geom_smooth,
    ggplot,
    labs,
    theme,
    theme_minimal,
)
from scipy import stats


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
    + geom_point(size=4, alpha=0.65, color="#306998")
    + geom_smooth(method="lm", se=True, color="#FFD43B", fill="#FFD43B", alpha=0.3, size=2)
    + annotate("text", x=2, y=92, label=annotation_text, ha="left", va="top", size=14, color="#333333")
    + labs(title="scatter-regression-linear · plotnine · pyplots.ai", x="Study Hours", y="Exam Score (%)")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major=element_line(color="#cccccc", alpha=0.3),
        panel_grid_minor=element_line(color="#dddddd", alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
