""" pyplots.ai
rose-basic: Basic Rose Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import math

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_text,
    geom_line,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Data - Monthly rainfall (mm) for a temperate climate
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [78, 62, 55, 48, 52, 68, 82, 85, 72, 88, 95, 82]

n = len(months)

# Create wedge polygons for each month
# Each wedge is a triangle from center to the arc
wedge_rows = []
n_arc_points = 30  # Points along the arc for smooth edges

for i, (month, value) in enumerate(zip(months, rainfall, strict=True)):
    # Starting angle (12 o'clock = pi/2, going clockwise)
    # Adjust so January is at top (index 0 starts at pi/2)
    # Use negative direction for clockwise motion
    start_angle = math.pi / 2 - (i * 2 * math.pi / n)
    end_angle = math.pi / 2 - ((i + 1) * 2 * math.pi / n)

    # Small gap between wedges
    gap = 0.02
    start_angle += gap
    end_angle -= gap

    # Center point
    wedge_rows.append({"x": 0, "y": 0, "month": month, "order": 0})

    # Arc points
    arc_angles = np.linspace(start_angle, end_angle, n_arc_points)
    for j, angle in enumerate(arc_angles):
        x = value * math.cos(angle)
        y = value * math.sin(angle)
        wedge_rows.append({"x": x, "y": y, "month": month, "order": j + 1})

    # Close back to center
    wedge_rows.append({"x": 0, "y": 0, "month": month, "order": n_arc_points + 1})

df = pd.DataFrame(wedge_rows)

# Preserve month order
df["month"] = pd.Categorical(df["month"], categories=months, ordered=True)

# Colors - gradient based on rainfall values
# Using Python Blue (#306998) as base with varying intensity
base_blue = np.array([48, 105, 152])  # RGB for #306998
python_yellow = np.array([255, 212, 59])  # RGB for #FFD43B

# Normalize rainfall for color mapping
min_val, max_val = min(rainfall), max(rainfall)
colors = []
for value in rainfall:
    t = (value - min_val) / (max_val - min_val)  # 0 to 1
    # Interpolate from blue to yellow
    rgb = (1 - t) * base_blue + t * python_yellow
    colors.append(f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}")

color_dict = dict(zip(months, colors, strict=True))

# Create radial gridlines (circles at 20, 40, 60, 80, 100)
grid_rows = []
grid_angles = np.linspace(0, 2 * math.pi, 101)
for radius in [20, 40, 60, 80, 100]:
    for angle in grid_angles:
        grid_rows.append({"x": radius * math.cos(angle), "y": radius * math.sin(angle), "radius": radius})

grid_df = pd.DataFrame(grid_rows)

# Create spoke lines (one for each month boundary)
spoke_rows = []
for i in range(n):
    angle = math.pi / 2 - (i * 2 * math.pi / n)
    spoke_rows.append({"x": 0, "y": 0, "spoke_id": i})
    spoke_rows.append({"x": 105 * math.cos(angle), "y": 105 * math.sin(angle), "spoke_id": i})

spoke_df = pd.DataFrame(spoke_rows)

# Create month labels positioned outside the chart
label_rows = []
for i, month in enumerate(months):
    # Center angle of each month's wedge
    center_angle = math.pi / 2 - ((i + 0.5) * 2 * math.pi / n)
    label_rows.append({"label": month, "x": 115 * math.cos(center_angle), "y": 115 * math.sin(center_angle)})

label_df = pd.DataFrame(label_rows)

# Create value labels on gridlines
value_label_rows = []
for radius in [20, 40, 60, 80, 100]:
    value_label_rows.append({"label": str(radius), "x": 5, "y": radius + 3})

value_label_df = pd.DataFrame(value_label_rows)

# Plot
plot = (
    ggplot()
    # Gridlines (circles)
    + geom_line(
        aes(x="x", y="y", group="radius"), data=grid_df, color="#CCCCCC", size=0.5, alpha=0.6, linetype="dashed"
    )
    # Spoke lines
    + geom_line(aes(x="x", y="y", group="spoke_id"), data=spoke_df, color="#DDDDDD", size=0.3, alpha=0.5)
    # Rose wedges
    + geom_polygon(aes(x="x", y="y", fill="month", group="month"), data=df, color="#2C3E50", size=0.3, alpha=0.85)
    # Month labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=14, fontweight="bold", color="#333333")
    # Value labels
    + geom_text(aes(x="x", y="y", label="label"), data=value_label_df, size=10, color="#666666")
    # Colors
    + scale_fill_manual(values=color_dict)
    # Axis scaling
    + scale_x_continuous(limits=(-135, 135))
    + scale_y_continuous(limits=(-135, 135))
    # Labels and title
    + labs(title="Monthly Rainfall (mm) · rose-basic · plotnine · pyplots.ai")
    # Theme for clean rose chart appearance
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=22, ha="center"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_background=element_blank(),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300)
