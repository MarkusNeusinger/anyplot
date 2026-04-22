""" pyplots.ai
cat-box-strip: Box Plot with Strip Overlay
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Data - Performance scores across departments
np.random.seed(42)

departments = ["Engineering", "Marketing", "Sales", "Support"]
n_per_dept = [35, 28, 32, 25]

data = []
for dept, n in zip(departments, n_per_dept, strict=True):
    if dept == "Engineering":
        # Slightly higher scores with some high performers
        scores = np.concatenate(
            [
                np.random.normal(78, 8, n - 3),
                np.array([95, 97, 42]),  # High performers and one outlier
            ]
        )
    elif dept == "Marketing":
        # Wider spread
        scores = np.random.normal(72, 12, n)
    elif dept == "Sales":
        # Bimodal-ish with some low outliers
        scores = np.concatenate(
            [
                np.random.normal(75, 7, n - 2),
                np.array([35, 38]),  # Low outliers
            ]
        )
    else:  # Support
        # Tighter distribution
        scores = np.random.normal(70, 6, n)

    scores = np.clip(scores, 20, 100)
    for score in scores:
        data.append({"Department": dept, "Performance Score": score})

df = pd.DataFrame(data)

# Plot - box plot with jittered strip overlay
plot = (
    ggplot(df, aes(x="Department", y="Performance Score"))
    + geom_boxplot(fill="#306998", color="#1a3d5c", alpha=0.6, width=0.6, outlier_alpha=0)
    + geom_jitter(color="#FFD43B", size=4, alpha=0.7, width=0.15)
    + labs(title="cat-box-strip · letsplot · pyplots.ai", x="Department", y="Performance Score")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save - use absolute path to current directory
output_dir = os.path.dirname(os.path.abspath(__file__))
ggsave(plot, os.path.join(output_dir, "plot.png"), scale=3)
ggsave(plot, os.path.join(output_dir, "plot.html"))
