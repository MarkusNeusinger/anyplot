""" pyplots.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Titanic-style survival data by passenger class
np.random.seed(42)

data = {
    "class": ["First", "First", "Second", "Second", "Third", "Third"],
    "survival": ["Survived", "Did Not Survive", "Survived", "Did Not Survive", "Survived", "Did Not Survive"],
    "count": [203, 122, 118, 167, 178, 528],
}
df = pd.DataFrame(data)
survival_order = ["Survived", "Did Not Survive"]

# Calculate proportions for mosaic plot
total = df["count"].sum()

# Calculate widths (proportional to class totals)
class_totals = df.groupby("class")["count"].sum()
class_order = ["First", "Second", "Third"]
widths = {c: class_totals[c] / total for c in class_order}

# Build rectangles for mosaic plot
gap = 0.02  # Gap between rectangles
rects = []
x_pos = 0

for cls in class_order:
    class_data = df[df["class"] == cls]
    class_total = class_data["count"].sum()
    width = widths[cls] - gap

    y_pos = 0
    # Use consistent survival order (Survived at bottom)
    for surv in survival_order:
        row = class_data[class_data["survival"] == surv].iloc[0]
        height = (row["count"] / class_total) * (1 - gap)
        rects.append(
            {
                "xmin": x_pos,
                "xmax": x_pos + width,
                "ymin": y_pos,
                "ymax": y_pos + height,
                "class": cls,
                "survival": row["survival"],
                "count": row["count"],
                "x_center": x_pos + width / 2,
                "y_center": y_pos + height / 2,
            }
        )
        y_pos += height + gap / 2

    x_pos += widths[cls]

rect_df = pd.DataFrame(rects)

# Colors - Python Blue for survived, muted for did not survive
colors = {"Survived": "#306998", "Did Not Survive": "#8B9DC3"}

# Create plot
plot = (
    ggplot(rect_df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="survival"), color="white", size=1.5)
    + geom_text(aes(x="x_center", y="y_center", label="count"), color="white", size=14, fontweight="bold")
    + scale_fill_manual(values=colors)
    + labs(
        title="mosaic-categorical · plotnine · pyplots.ai",
        x="Passenger Class (width proportional to class size)",
        y="Survival Proportion",
        fill="Outcome",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        panel_grid=element_blank(),
    )
)

# Add class labels at bottom
class_labels = pd.DataFrame(
    {
        "x": [
            widths["First"] / 2,
            widths["First"] + widths["Second"] / 2,
            widths["First"] + widths["Second"] + widths["Third"] / 2,
        ],
        "y": [-0.06, -0.06, -0.06],
        "label": class_order,
    }
)

plot = plot + geom_text(
    data=class_labels, mapping=aes(x="x", y="y", label="label"), size=14, color="#306998", fontweight="bold"
)

plot.save("plot.png", dpi=300, width=16, height=9)
