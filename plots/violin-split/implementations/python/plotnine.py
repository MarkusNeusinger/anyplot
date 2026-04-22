""" pyplots.ai
violin-split: Split Violin Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_text,
    geom_boxplot,
    geom_violin,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Employee satisfaction scores before and after training program
np.random.seed(42)

categories = ["Engineering", "Marketing", "Sales", "Support"]

data = []
for category in categories:
    # Generate different distributions for each category and time point
    if category == "Engineering":
        before = np.random.normal(65, 12, 80)
        after = np.random.normal(78, 10, 80)
    elif category == "Marketing":
        before = np.random.normal(58, 15, 100)
        after = np.random.normal(72, 12, 100)
    elif category == "Sales":
        before = np.random.normal(70, 10, 90)
        after = np.random.normal(82, 8, 90)
    else:  # Support
        before = np.random.normal(55, 18, 70)
        after = np.random.normal(75, 14, 70)

    for val in before:
        data.append({"category": category, "value": val, "split_group": "Before Training"})
    for val in after:
        data.append({"category": category, "value": val, "split_group": "After Training"})

df = pd.DataFrame(data)

# Clip values to realistic range (0-100 for satisfaction scores)
df["value"] = df["value"].clip(0, 100)

# Plot - True split violin with left-right style for side-by-side halves
# Added inner boxplots and visible grid lines as per review feedback
plot = (
    ggplot(df, aes(x="category", y="value", fill="split_group"))
    + geom_violin(style="left-right", alpha=0.8, size=0.8, scale="width", trim=True)
    + geom_boxplot(width=0.15, alpha=0.9, outlier_alpha=0.5, outlier_size=2, size=0.6, position="identity")
    + scale_fill_manual(values=["#306998", "#FFD43B"])
    + labs(x="Department", y="Satisfaction Score (0-100)", fill="Period", title="violin-split · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_text(size=20),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major_y=element_line(color="#cccccc", alpha=0.3, linetype="dashed"),
        panel_grid_major_x=element_line(color="#cccccc", alpha=0.2),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
