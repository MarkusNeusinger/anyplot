""" pyplots.ai
polar-basic: Basic Polar Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import math

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Hourly temperature readings (24 hours)
np.random.seed(42)
hours = np.arange(0, 24)
# Temperature pattern: cooler at night, warmer during day
base_temp = 15 + 10 * np.sin((hours - 6) * math.pi / 12)
temperatures = base_temp + np.random.randn(24) * 2

# Convert polar coordinates (theta=hour, r=temperature) to cartesian
# theta in radians: 0 hours = top (90 degrees), clockwise
theta = (90 - hours * 15) * math.pi / 180  # 15 degrees per hour, starting at top

# Normalize temperatures to positive radius (shift to ensure positive values)
radius = temperatures - temperatures.min() + 5  # Ensure minimum radius of 5

# Convert to x, y
x = radius * np.cos(theta)
y = radius * np.sin(theta)

df = pd.DataFrame({"hour": hours, "temperature": temperatures, "x": x, "y": y})

# Create radial gridlines (circles at different radii) using geom_path
max_radius = radius.max() + 5
grid_radii = np.linspace(5, max_radius, 5)
circle_angles = np.linspace(0, 2 * math.pi, 101)  # 101 points to close circle

grid_rows = []
for i, r in enumerate(grid_radii):
    for angle in circle_angles:
        grid_rows.append({"x": r * np.cos(angle), "y": r * np.sin(angle), "circle_id": i})

grid_df = pd.DataFrame(grid_rows)

# Create angular gridlines (spokes) at major hour positions
spoke_rows = []
major_hours = [0, 3, 6, 9, 12, 15, 18, 21]  # Every 3 hours
for hour in major_hours:
    angle = (90 - hour * 15) * math.pi / 180
    spoke_rows.append(
        {"x": 0, "y": 0, "xend": (max_radius + 3) * np.cos(angle), "yend": (max_radius + 3) * np.sin(angle)}
    )

spoke_df = pd.DataFrame(spoke_rows)

# Create hour labels
label_rows = []
hour_labels = {0: "00:00", 3: "03:00", 6: "06:00", 9: "09:00", 12: "12:00", 15: "15:00", 18: "18:00", 21: "21:00"}
for hour, label in hour_labels.items():
    angle = (90 - hour * 15) * math.pi / 180
    label_rows.append({"label": label, "x": (max_radius + 8) * np.cos(angle), "y": (max_radius + 8) * np.sin(angle)})

label_df = pd.DataFrame(label_rows)

# Create radial axis labels showing temperature scale (placed along 3 o'clock spoke)
radial_label_rows = []
temp_min = temperatures.min()
for r in grid_radii:
    # Convert radius back to temperature
    temp_value = temp_min + (r - 5)
    radial_label_rows.append({"label": f"{temp_value:.0f}°C", "x": r + 2, "y": -2})

radial_label_df = pd.DataFrame(radial_label_rows)

# Create data path (closing the loop)
df_sorted = df.sort_values("hour")
# Add first point to end to close the loop
df_path = pd.concat([df_sorted, df_sorted.iloc[[0]]], ignore_index=True)

# Plot
plot = (
    ggplot()
    # Radial gridlines (circles) using geom_path with group
    + geom_path(
        aes(x="x", y="y", group="circle_id"), data=grid_df, color="#CCCCCC", size=0.5, alpha=0.5, linetype="dashed"
    )
    # Angular gridlines (spokes)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=spoke_df, color="#CCCCCC", size=0.5, alpha=0.7)
    # Data line (closed loop)
    + geom_path(aes(x="x", y="y"), data=df_path, color="#306998", size=1.5, alpha=0.7)
    # Data points
    + geom_point(aes(x="x", y="y"), data=df, color="#306998", size=6, alpha=0.8)
    # Hour labels
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=14, color="#333333")
    # Radial axis labels (temperature scale)
    + geom_text(aes(x="x", y="y", label="label"), data=radial_label_df, size=11, color="#666666")
    # Styling
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-max_radius - 10, max_radius + 10))
    + scale_y_continuous(limits=(-max_radius - 10, max_radius + 10))
    + labs(title="polar-basic · letsplot · pyplots.ai", x="", y="")
    + ggsize(1200, 1200)
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
    )
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
