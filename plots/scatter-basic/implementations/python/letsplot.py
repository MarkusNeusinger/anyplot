""" pyplots.ai
scatter-basic: Basic Scatter Plot
Library: letsplot 4.8.2 | Python 3.14
Quality: 91/100 | Created: 2025-12-22
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Study hours vs exam scores with varied density and outliers
np.random.seed(42)
n = 130
study_hours = np.concatenate(
    [
        np.random.uniform(1, 10, 110),
        np.random.uniform(7, 9.5, 12),  # denser cluster at high study hours
        np.array([2.0, 1.5, 3.0, 9.5, 8.5, 2.5, 1.8, 4.0]),  # outliers
    ]
)
exam_scores = np.concatenate(
    [
        study_hours[:110] * 8 + 20 + np.random.randn(110) * 5,
        study_hours[110:122] * 8 + 22 + np.random.randn(12) * 3,
        np.array([75, 82, 70, 55, 48, 68, 78, 90]),  # outliers (high scores with low hours & vice versa)
    ]
)

df = pd.DataFrame({"study_hours": study_hours, "exam_scores": exam_scores})

# Compute correlation for annotation
corr = df["study_hours"].corr(df["exam_scores"])

# Plot with trend line and storytelling annotation
plot = (
    ggplot(df, aes(x="study_hours", y="exam_scores"))  # noqa: F405
    + geom_point(  # noqa: F405
        fill="#306998",
        color="white",
        size=5,
        alpha=0.65,
        stroke=0.7,
        shape=21,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Study Hours|@{study_hours}{.1f}")
        .line("Exam Score|@{exam_scores}{.1f}"),
    )
    + geom_smooth(  # noqa: F405
        method="lm", color="#E3882D", size=1.2, alpha=0.15, fill="#E3882D"
    )
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=pd.DataFrame({"x": [8.3], "y": [38], "label": [f"r = {corr:.2f}"]}),
        size=14,
        color="#444444",
        family="monospace",
    )
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=pd.DataFrame({"x": [2.0], "y": [83], "label": ["outliers →"]}),
        size=11,
        color="#888888",
        fontface="italic",
    )
    + labs(  # noqa: F405
        x="Study Hours (hrs)",
        y="Exam Score (points)",
        title="scatter-basic · letsplot · pyplots.ai",
        caption="Linear trend with 95% confidence band",
    )
    + scale_x_continuous(  # noqa: F405
        breaks=[2, 4, 6, 8, 10], expand=[0.03, 0]
    )
    + scale_y_continuous(  # noqa: F405
        breaks=[30, 45, 60, 75, 90, 105], expand=[0.03, 0]
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#555555"),  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        plot_title=element_text(size=24, color="#222222", face="bold"),  # noqa: F405
        plot_caption=element_text(size=13, color="#999999", face="italic"),  # noqa: F405
        panel_grid_major=element_line(color="#E8E8E8", size=0.35),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),  # noqa: F405
        panel_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),  # noqa: F405
        axis_ticks=element_line(color="#CCCCCC", size=0.3),  # noqa: F405
        plot_margin=[30, 40, 20, 20],
    )
)

# Save PNG (scale 3x to get 4800 x 2700 px)
export_ggsave(plot, filename="plot.png", path=".", scale=3)

# Save HTML for interactive version
export_ggsave(plot, filename="plot.html", path=".")
