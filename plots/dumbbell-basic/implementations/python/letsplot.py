""" pyplots.ai
dumbbell-basic: Basic Dumbbell Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Employee satisfaction scores before and after policy changes
categories = [
    "Engineering",
    "Marketing",
    "Sales",
    "Customer Support",
    "HR",
    "Finance",
    "Operations",
    "Product",
    "Legal",
    "R&D",
]
before_scores = [62, 58, 71, 55, 68, 64, 59, 73, 66, 61]
after_scores = [78, 72, 85, 74, 81, 76, 71, 88, 79, 75]

df = pd.DataFrame({"category": categories, "before": before_scores, "after": after_scores})

# Calculate difference for sorting - sort by improvement (largest first)
df["diff"] = df["after"] - df["before"]
df = df.sort_values("diff", ascending=True).reset_index(drop=True)

# Create numeric y positions for categories (horizontal orientation)
df["y_pos"] = range(len(df))

# Create long-format data for points (to get legend)
df_points = pd.concat(
    [
        pd.DataFrame({"y_pos": df["y_pos"], "value": df["before"], "period": "Before"}),
        pd.DataFrame({"y_pos": df["y_pos"], "value": df["after"], "period": "After"}),
    ]
)

# Plot - Horizontal dumbbell chart
plot = (
    ggplot()
    # Connecting lines - thin and subtle
    + geom_segment(data=df, mapping=aes(x="before", xend="after", y="y_pos", yend="y_pos"), size=1.5, color="#888888")
    # Points with color mapping for legend
    + geom_point(data=df_points, mapping=aes(x="value", y="y_pos", color="period"), size=8)
    + scale_color_manual(values=["#FFD43B", "#306998"], name="Period")
    + labs(
        x="Satisfaction Score", y="Department", title="Employee Satisfaction · dumbbell-basic · letsplot · pyplots.ai"
    )
    + scale_x_continuous(limits=[50, 95])
    + scale_y_continuous(breaks=list(range(len(df))), labels=df["category"].tolist())
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        axis_title=element_text(size=20),
        plot_title=element_text(size=24, hjust=0.5),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        panel_grid_major_y=element_blank(),
    )
)

# Save
ggsave(plot, filename="plot.png", path=".", scale=3)
ggsave(plot, filename="plot.html", path=".")
