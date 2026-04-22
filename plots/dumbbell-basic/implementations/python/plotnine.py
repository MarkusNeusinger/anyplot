""" pyplots.ai
dumbbell-basic: Basic Dumbbell Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Data: Employee satisfaction scores before and after workplace policy changes
categories = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", "Customer Support", "Product"]
before_scores = [65, 58, 72, 45, 68, 52, 40, 75]
after_scores = [82, 71, 78, 73, 75, 68, 62, 88]

# Calculate differences and sort by largest improvement first
differences = [a - b for a, b in zip(after_scores, before_scores, strict=True)]
sorted_data = sorted(
    zip(categories, before_scores, after_scores, differences, strict=True), key=lambda x: x[3], reverse=True
)
categories = [d[0] for d in sorted_data]
before_scores = [d[1] for d in sorted_data]
after_scores = [d[2] for d in sorted_data]

# Create DataFrame for segments (connecting lines)
df_segments = pd.DataFrame({"category": categories, "start": before_scores, "end": after_scores})

# Create DataFrame for points (long format for legend)
df_points = pd.DataFrame(
    {
        "category": categories * 2,
        "value": before_scores + after_scores,
        "period": ["Before"] * len(categories) + ["After"] * len(categories),
    }
)

# Create ordered categorical for proper y-axis ordering
df_segments["category"] = pd.Categorical(df_segments["category"], categories=categories, ordered=True)
df_points["category"] = pd.Categorical(df_points["category"], categories=categories, ordered=True)

# Plot
plot = (
    ggplot()
    # Connecting lines (thin and subtle)
    + geom_segment(
        aes(x="start", xend="end", y="category", yend="category"), data=df_segments, color="#888888", size=1.5
    )
    # Dots with distinct colors for before/after
    + geom_point(aes(x="value", y="category", color="period"), data=df_points, size=6, stroke=0.5)
    + scale_color_manual(values={"Before": "#306998", "After": "#FFD43B"})
    + scale_x_continuous(limits=(30, 100))
    + labs(x="Satisfaction Score", y="Department", title="dumbbell-basic · plotnine · pyplots.ai", color="")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major_y=element_blank(),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
