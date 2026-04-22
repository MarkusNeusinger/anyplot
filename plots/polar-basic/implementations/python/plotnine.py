""" pyplots.ai
polar-basic: Basic Polar Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import math

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Data - Hourly activity levels throughout the day (cyclical pattern)
np.random.seed(42)
hours = np.arange(0, 24)
# Activity pattern: low at night, peak in morning and evening
base_activity = 20 + 40 * np.sin((hours - 6) * np.pi / 12) ** 2
activity = base_activity + np.random.uniform(-8, 8, 24)
activity = np.clip(activity, 5, 100)

# Convert hours to angles (0 hours = top, clockwise)
# Offset by -90 degrees to start at top
theta = hours * 2 * math.pi / 24 - math.pi / 2

# Convert polar to Cartesian coordinates
x = activity * np.cos(theta)
y = activity * np.sin(theta)

# Create main dataframe
df = pd.DataFrame({"hour": hours, "activity": activity, "theta": theta, "x": x, "y": y})

# Close the loop by adding first point at end
df_closed = pd.concat([df, df.iloc[[0]]], ignore_index=True)

# Create circular gridlines (at 25, 50, 75, 100 radius)
grid_rows = []
grid_angles = np.linspace(0, 2 * np.pi, 101)
for radius in [25, 50, 75, 100]:
    for angle in grid_angles:
        grid_rows.append({"x": radius * np.cos(angle), "y": radius * np.sin(angle), "radius": radius})

grid_df = pd.DataFrame(grid_rows)

# Create radial spokes (every 3 hours = 8 spokes)
spoke_rows = []
spoke_hours = [0, 3, 6, 9, 12, 15, 18, 21]
for h in spoke_hours:
    angle = h * 2 * math.pi / 24 - math.pi / 2
    spoke_rows.append({"x1": 0, "y1": 0, "x2": 105 * np.cos(angle), "y2": 105 * np.sin(angle)})

spoke_df = pd.DataFrame(spoke_rows)

# Create hour labels (positioned outside the chart)
label_rows = []
for h in spoke_hours:
    angle = h * 2 * math.pi / 24 - math.pi / 2
    label_text = f"{h:02d}:00"
    label_rows.append({"label": label_text, "x": 120 * np.cos(angle), "y": 120 * np.sin(angle)})

label_df = pd.DataFrame(label_rows)

# Create radius labels (on the right side, angle=0)
radius_labels = []
for r in [25, 50, 75, 100]:
    radius_labels.append({"label": str(r), "x": r + 5, "y": 5})

radius_label_df = pd.DataFrame(radius_labels)

# Plot
plot = (
    ggplot()
    # Circular gridlines
    + geom_path(
        aes(x="x", y="y", group="radius"), data=grid_df, color="#CCCCCC", size=0.5, alpha=0.6, linetype="dashed"
    )
    # Radial spokes
    + geom_segment(aes(x="x1", y="y1", xend="x2", yend="y2"), data=spoke_df, color="#CCCCCC", size=0.5, alpha=0.6)
    # Data line (connecting all points)
    + geom_path(aes(x="x", y="y"), data=df_closed, color="#306998", size=1.5, alpha=0.9)
    # Data points
    + geom_point(aes(x="x", y="y"), data=df, color="#306998", fill="#FFD43B", size=4, stroke=1.5)
    # Hour labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=14, color="#333333")
    # Radius value labels
    + geom_text(aes(x="x", y="y", label="label"), data=radius_label_df, size=10, color="#666666", ha="left")
    # Equal coordinate system for proper circle
    + coord_fixed(ratio=1)
    # Axis scaling with padding
    + scale_x_continuous(limits=(-140, 140))
    + scale_y_continuous(limits=(-140, 140))
    # Title
    + labs(title="Hourly Activity Levels · polar-basic · plotnine · pyplots.ai")
    # Clean polar-style theme
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_blank(),
        plot_background=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300)
