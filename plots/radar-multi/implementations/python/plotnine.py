""" pyplots.ai
radar-multi: Multi-Series Radar Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-25
"""

import math

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_line,
    geom_point,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Data - Product comparison across key attributes
categories = ["Price", "Quality", "Durability", "Support", "Features", "Design"]
n = len(categories)

# Four products for comparison (scale 0-100)
products = {
    "Product A": [85, 90, 75, 80, 70, 85],
    "Product B": [70, 75, 90, 65, 85, 70],
    "Product C": [95, 60, 70, 90, 75, 60],
    "Product D": [60, 80, 85, 75, 90, 80],
}

# Create angles for each category (evenly spaced around circle)
angles = [i * 2 * math.pi / n for i in range(n)]

# Build dataframe with x,y coordinates for polar plotting
# For radar chart, we need to close each polygon by repeating first point
data_rows = []
for series_name, values in products.items():
    for i, (cat, val, angle) in enumerate(zip(categories, values, angles, strict=True)):
        data_rows.append({"category": cat, "value": val, "angle": angle, "series": series_name, "order": i})
    # Close the polygon
    data_rows.append(
        {"category": categories[0], "value": values[0], "angle": angles[0], "series": series_name, "order": n}
    )

df = pd.DataFrame(data_rows)

# Convert to cartesian coordinates for plotting
df["x"] = df["value"] * np.cos(df["angle"] - math.pi / 2)
df["y"] = df["value"] * np.sin(df["angle"] - math.pi / 2)

# Create gridlines data (circles at 20, 40, 60, 80, 100)
grid_rows = []
grid_angles = np.linspace(0, 2 * math.pi, 101)
for radius in [20, 40, 60, 80, 100]:
    for angle in grid_angles:
        grid_rows.append(
            {"x": radius * math.cos(angle - math.pi / 2), "y": radius * math.sin(angle - math.pi / 2), "radius": radius}
        )

grid_df = pd.DataFrame(grid_rows)

# Create axis lines (spokes)
spoke_rows = []
for angle in angles:
    spoke_rows.append({"x": 0, "y": 0, "angle_group": angle})
    spoke_rows.append(
        {"x": 105 * math.cos(angle - math.pi / 2), "y": 105 * math.sin(angle - math.pi / 2), "angle_group": angle}
    )

spoke_df = pd.DataFrame(spoke_rows)

# Create axis labels data (positioned just outside the chart)
label_rows = []
for cat, angle in zip(categories, angles, strict=True):
    label_rows.append(
        {"label": cat, "x": 120 * math.cos(angle - math.pi / 2), "y": 120 * math.sin(angle - math.pi / 2)}
    )

label_df = pd.DataFrame(label_rows)

# Define colors: Python Blue, Python Yellow, plus two more distinct colors
colors = ["#306998", "#FFD43B", "#E74C3C", "#2ECC71"]

# Plot
plot = (
    ggplot()
    # Gridlines (circles)
    + geom_line(
        aes(x="x", y="y", group="radius"), data=grid_df, color="#CCCCCC", size=0.5, alpha=0.7, linetype="dashed"
    )
    # Spokes
    + geom_line(aes(x="x", y="y", group="angle_group"), data=spoke_df, color="#CCCCCC", size=0.5, alpha=0.7)
    # Filled polygons for each series (with transparency for overlap visibility)
    + geom_polygon(aes(x="x", y="y", fill="series", group="series"), data=df, alpha=0.2)
    # Lines connecting points
    + geom_line(aes(x="x", y="y", color="series", group="series"), data=df, size=1.5)
    # Points at each vertex (exclude closing points)
    + geom_point(aes(x="x", y="y", color="series"), data=df[df["order"] < n], size=5)
    # Category labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=14, color="#333333")
    # Apply custom colors
    + scale_fill_manual(values=colors)
    + scale_color_manual(values=colors)
    # Axis scaling
    + scale_x_continuous(limits=(-150, 150))
    + scale_y_continuous(limits=(-150, 150))
    # Labels and title
    + labs(title="radar-multi · plotnine · pyplots.ai", fill="Product", color="Product")
    # Theme for clean radar appearance
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300)
