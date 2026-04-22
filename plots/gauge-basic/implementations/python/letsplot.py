""" pyplots.ai
gauge-basic: Basic Gauge Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import math

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_polygon,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Data - sales performance gauge
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Gauge parameters
inner_radius = 0.5
outer_radius = 1.0
n_points = 50

# Zone boundaries and colors
zone_boundaries = [min_value] + thresholds + [max_value]
zone_colors = {"Low": "#DC2626", "Medium": "#FFD43B", "High": "#22C55E"}
zone_names = ["Low", "Medium", "High"]

# Build arc polygons for each zone (semi-circle from 180° to 0°)
polygons_data = []
for i in range(len(zone_boundaries) - 1):
    start_val = zone_boundaries[i]
    end_val = zone_boundaries[i + 1]

    # Convert values to angles (180° at min, 0° at max)
    start_ratio = (start_val - min_value) / (max_value - min_value)
    end_ratio = (end_val - min_value) / (max_value - min_value)
    start_angle = 180 - start_ratio * 180
    end_angle = 180 - end_ratio * 180

    # Generate arc polygon coordinates
    angles = [math.radians(end_angle + (start_angle - end_angle) * j / n_points) for j in range(n_points + 1)]

    # Outer arc (clockwise)
    x_outer = [outer_radius * math.cos(a) for a in angles]
    y_outer = [outer_radius * math.sin(a) for a in angles]

    # Inner arc (counter-clockwise)
    x_inner = [inner_radius * math.cos(a) for a in reversed(angles)]
    y_inner = [inner_radius * math.sin(a) for a in reversed(angles)]

    x_coords = x_outer + x_inner
    y_coords = y_outer + y_inner

    for j, (x, y) in enumerate(zip(x_coords, y_coords, strict=True)):
        polygons_data.append({"x": x, "y": y, "zone": zone_names[i], "order": j})

df_polygons = pd.DataFrame(polygons_data)

# Calculate needle position
needle_ratio = (value - min_value) / (max_value - min_value)
needle_angle_deg = 180 - needle_ratio * 180
needle_angle = math.radians(needle_angle_deg)
needle_length = 0.85
needle_x_end = needle_length * math.cos(needle_angle)
needle_y_end = needle_length * math.sin(needle_angle)

df_needle = pd.DataFrame({"x": [0], "y": [0], "xend": [needle_x_end], "yend": [needle_y_end]})

# Center circle for needle pivot
circle_points = 30
circle_angles = [2 * math.pi * i / circle_points for i in range(circle_points + 1)]
circle_r = 0.08
df_circle = pd.DataFrame(
    {"x": [circle_r * math.cos(a) for a in circle_angles], "y": [circle_r * math.sin(a) for a in circle_angles]}
)

# Value label - prominently displayed below gauge
df_label = pd.DataFrame({"x": [0], "y": [-0.25], "label": [str(value)]})

# Min/Max labels at gauge edges
df_min_max = pd.DataFrame({"x": [-1.05, 1.05], "y": [-0.08, -0.08], "label": [str(min_value), str(max_value)]})

# Create plot
plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", fill="zone", group="zone"), data=df_polygons, color="#FFFFFF", size=1.5, alpha=0.9)
    + scale_fill_manual(values=zone_colors)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_needle, color="#1F2937", size=5)
    + geom_polygon(aes(x="x", y="y"), data=df_circle, fill="#1F2937", color="#1F2937")
    + geom_text(aes(x="x", y="y", label="label"), data=df_label, size=28, color="#1F2937", fontface="bold")
    + geom_text(aes(x="x", y="y", label="label"), data=df_min_max, size=14, color="#6B7280")
    + labs(title="gauge-basic · letsplot · pyplots.ai")
    + xlim(-1.4, 1.4)
    + ylim(-0.5, 1.3)
    + theme(
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_blank(),
        plot_background=element_blank(),
        legend_position="none",
        plot_title=element_text(size=24, face="bold"),
    )
    + ggsize(1600, 900)
)

# Save outputs
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")
