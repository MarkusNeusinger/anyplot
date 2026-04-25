""" anyplot.ai
gauge-basic: Basic Gauge Chart
Library: letsplot 4.9.0 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-25
"""

import math
import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
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

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

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
df_label = pd.DataFrame({"x": [0], "y": [-0.22], "label": [f"{value}%"]})

# Metric subtitle below value
df_subtitle = pd.DataFrame({"x": [0], "y": [-0.42], "label": ["Sales Performance Score"]})

# Min/Max labels at gauge edges
df_min_max = pd.DataFrame({"x": [-1.05, 1.05], "y": [-0.08, -0.08], "label": [str(min_value), str(max_value)]})

# Zone labels (Low/Medium/High) at arc zone midpoints
zone_label_radius = 0.75
df_zone_labels_rows = []
for i, name in enumerate(zone_names):
    start_val = zone_boundaries[i]
    end_val = zone_boundaries[i + 1]
    mid_ratio = ((start_val + end_val) / 2 - min_value) / (max_value - min_value)
    mid_angle = math.radians(180 - mid_ratio * 180)
    df_zone_labels_rows.append(
        {"x": zone_label_radius * math.cos(mid_angle), "y": zone_label_radius * math.sin(mid_angle), "label": name}
    )
df_zone_labels = pd.DataFrame(df_zone_labels_rows)

# Create plot
plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", fill="zone", group="zone"), data=df_polygons, color=PAGE_BG, size=1.5, alpha=0.9)
    + scale_fill_manual(values=zone_colors)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_needle, color=INK, size=5)
    + geom_polygon(aes(x="x", y="y"), data=df_circle, fill=INK, color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=df_label, size=28, color=INK, fontface="bold")
    + geom_text(aes(x="x", y="y", label="label"), data=df_subtitle, size=14, color=INK_SOFT)
    + geom_text(aes(x="x", y="y", label="label"), data=df_min_max, size=14, color=INK_SOFT)
    + geom_text(aes(x="x", y="y", label="label"), data=df_zone_labels, size=13, color=INK_SOFT, fontface="bold")
    + labs(title="gauge-basic · letsplot · anyplot.ai")
    + xlim(-1.4, 1.4)
    + ylim(-0.55, 1.15)
    + theme(
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        legend_position="none",
        plot_title=element_text(size=24, face="bold", color=INK),
    )
    + ggsize(1600, 900)
)

# Save outputs
ggsave(plot, f"plot-{THEME}.png", scale=3, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
