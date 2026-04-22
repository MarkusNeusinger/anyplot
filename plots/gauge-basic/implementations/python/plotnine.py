""" pyplots.ai
gauge-basic: Basic Gauge Chart
Library: plotnine 0.15.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-14
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_blank,
    geom_point,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)


# Data
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Gauge parameters
inner_radius = 0.5
outer_radius = 1.0
start_angle = np.pi  # 180 degrees (left)
end_angle = 0  # 0 degrees (right)

# Create color zones based on thresholds
zones = []
zone_colors = ["#E74C3C", "#F1C40F", "#27AE60"]  # Red, Yellow, Green
zone_bounds = [min_value] + thresholds + [max_value]

for i in range(len(zone_bounds) - 1):
    start_pct = (zone_bounds[i] - min_value) / (max_value - min_value)
    end_pct = (zone_bounds[i + 1] - min_value) / (max_value - min_value)

    # Create arc segment as polygon
    start_ang = start_angle - start_pct * (start_angle - end_angle)
    end_ang = start_angle - end_pct * (start_angle - end_angle)
    n_points = 50

    angles_outer = np.linspace(start_ang, end_ang, n_points)
    angles_inner = np.linspace(end_ang, start_ang, n_points)

    x = np.concatenate([outer_radius * np.cos(angles_outer), inner_radius * np.cos(angles_inner)])
    y = np.concatenate([outer_radius * np.sin(angles_outer), inner_radius * np.sin(angles_inner)])

    for j in range(len(x)):
        zones.append({"x": x[j], "y": y[j], "zone": i, "color": zone_colors[i]})

df_zones = pd.DataFrame(zones)

# Create needle pointing to value
value_pct = (value - min_value) / (max_value - min_value)
needle_angle = start_angle - value_pct * (start_angle - end_angle)
needle_length = outer_radius * 0.85

df_needle = pd.DataFrame(
    {"x": [0], "y": [0], "xend": [needle_length * np.cos(needle_angle)], "yend": [needle_length * np.sin(needle_angle)]}
)

# Create tick marks and labels
tick_values = [0, 25, 50, 75, 100]
tick_data = []
label_data = []
tick_inner = outer_radius * 1.02
tick_outer = outer_radius * 1.08
label_radius = outer_radius * 1.18

for tv in tick_values:
    pct = (tv - min_value) / (max_value - min_value)
    ang = start_angle - pct * (start_angle - end_angle)
    tick_data.append(
        {
            "x": tick_inner * np.cos(ang),
            "y": tick_inner * np.sin(ang),
            "xend": tick_outer * np.cos(ang),
            "yend": tick_outer * np.sin(ang),
        }
    )
    label_data.append({"x": label_radius * np.cos(ang), "y": label_radius * np.sin(ang), "label": str(tv)})

df_ticks = pd.DataFrame(tick_data)
df_labels = pd.DataFrame(label_data)

# Value display label
df_value = pd.DataFrame({"x": [0], "y": [-0.2], "label": [str(value)]})

# Title label
df_title = pd.DataFrame({"x": [0], "y": [1.45], "label": ["gauge-basic · plotnine · pyplots.ai"]})

# Build the plot
plot = (
    ggplot()
    # Draw zone arcs as polygons grouped by zone
    + geom_polygon(aes(x="x", y="y", fill="factor(zone)", group="zone"), data=df_zones, color="white", size=0.5)
    # Draw tick marks
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_ticks, color="#2C3E50", size=1.5)
    # Draw tick labels
    + geom_text(aes(x="x", y="y", label="label"), data=df_labels, color="#2C3E50", size=16)
    # Draw needle
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_needle, color="#2C3E50", size=3)
    # Draw needle center circle
    + geom_point(aes(x="x", y="y"), data=pd.DataFrame({"x": [0], "y": [0]}), color="#2C3E50", size=8)
    # Draw value label
    + geom_text(aes(x="x", y="y", label="label"), data=df_value, color="#2C3E50", size=24, fontweight="bold")
    # Draw title
    + geom_text(aes(x="x", y="y", label="label"), data=df_title, color="#2C3E50", size=14)
    + coord_fixed(ratio=1, xlim=(-1.5, 1.5), ylim=(-0.5, 1.6))
    + labs(x="", y="")
    + theme_void()
    + theme(figure_size=(16, 9), legend_position="none", plot_background=element_blank())
    # Manual fill colors for zones
    + scale_fill_manual(values=zone_colors)
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
