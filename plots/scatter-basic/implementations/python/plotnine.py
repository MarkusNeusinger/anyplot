""" pyplots.ai
scatter-basic: Basic Scatter Plot
Library: plotnine 0.15.3 | Python 3.14
Quality: 93/100 | Created: 2025-12-22
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    stat_smooth,
    theme,
    theme_minimal,
)


# Data: Study hours vs exam scores (realistic educational context)
np.random.seed(42)
n_points = 150
study_hours = np.random.uniform(1, 10, n_points)
base_scores = 35 + study_hours * 6
noise = np.random.randn(n_points) * 7
exam_scores = np.clip(base_scores + noise, 15, 100)

df = pd.DataFrame({"study_hours": study_hours, "exam_scores": exam_scores})

# Compute correlation for annotation
correlation = df["study_hours"].corr(df["exam_scores"])

# Plot
plot = (
    ggplot(df, aes(x="study_hours", y="exam_scores"))
    + geom_point(fill="#306998", color="#1a3a5c", shape="o", alpha=0.65, size=5, stroke=0.3)
    + stat_smooth(method="lm", color="#e3822a", size=1.2, alpha=0.15, linetype="solid")
    + annotate("text", x=2.0, y=97, label=f"r = {correlation:.2f}", size=14, color="#444444", fontstyle="italic")
    + annotate("text", x=2.0, y=92, label="Strong positive correlation", size=10, color="#777777")
    + scale_x_continuous(breaks=range(1, 11), limits=(0.5, 10.5))
    + scale_y_continuous(breaks=range(20, 101, 10), limits=(10, 105))
    + labs(
        x="Study Hours (per week)",
        y="Exam Score (points)",
        title="scatter-basic · plotnine · pyplots.ai",
        subtitle="More study time correlates with higher exam performance",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#333333"),
        axis_title=element_text(size=20, weight="bold", color="#222222"),
        axis_text=element_text(size=16, color="#555555"),
        plot_title=element_text(size=24, weight="bold", color="#1a1a1a"),
        plot_subtitle=element_text(size=17, color="#666666"),
        panel_grid_major=element_line(color="#e0e0e0", size=0.4),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="#fafafa", color="white"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
