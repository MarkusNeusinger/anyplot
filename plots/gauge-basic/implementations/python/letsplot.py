""" anyplot.ai
gauge-basic: Basic Gauge Chart
Library: letsplot 4.11.0 | Python 3.13.14
Quality: 89/100 | Updated: 2026-06-30
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
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — semantic exception for gauge zones
# bad/low → matte red (#AE3030), caution/medium → amber (#DDCC77), good/high → brand green (#009E73)
zone_colors_map = {"Low": "#AE3030", "Medium": "#DDCC77", "High": "#009E73"}

# Sales performance gauge data
value = 72
min_value = 0
max_value = 100
thresholds = [30, 70]

# Gauge geometry parameters
inner_radius = 0.5
outer_radius = 1.0
n_points = 50

zone_boundaries = [min_value] + thresholds + [max_value]
zone_names = ["Low", "Medium", "High"]

# Build arc polygon for each zone (semi-circle: 180° → 0°)
polygons_data = []
for i in range(len(zone_boundaries) - 1):
    start_val = zone_boundaries[i]
    end_val = zone_boundaries[i + 1]

    start_ratio = (start_val - min_value) / (max_value - min_value)
    end_ratio = (end_val - min_value) / (max_value - min_value)
    start_angle = 180 - start_ratio * 180
    end_angle = 180 - end_ratio * 180

    angles = [math.radians(end_angle + (start_angle - end_angle) * j / n_points) for j in range(n_points + 1)]

    x_outer = [outer_radius * math.cos(a) for a in angles]
    y_outer = [outer_radius * math.sin(a) for a in angles]
    x_inner = [inner_radius * math.cos(a) for a in reversed(angles)]
    y_inner = [inner_radius * math.sin(a) for a in reversed(angles)]

    for j, (x, y) in enumerate(zip(x_outer + x_inner, y_outer + y_inner, strict=True)):
        polygons_data.append({"x": x, "y": y, "zone": zone_names[i], "order": j})

df_polygons = pd.DataFrame(polygons_data)

# Needle
needle_ratio = (value - min_value) / (max_value - min_value)
needle_angle = math.radians(180 - needle_ratio * 180)
needle_length = 0.85
df_needle = pd.DataFrame(
    {
        "x": [0],
        "y": [0],
        "xend": [needle_length * math.cos(needle_angle)],
        "yend": [needle_length * math.sin(needle_angle)],
    }
)

# Pivot circle
circle_r = 0.08
circle_angles = [2 * math.pi * i / 30 for i in range(31)]
df_circle = pd.DataFrame(
    {"x": [circle_r * math.cos(a) for a in circle_angles], "y": [circle_r * math.sin(a) for a in circle_angles]}
)

# Text elements
df_label = pd.DataFrame({"x": [0], "y": [-0.22], "label": [f"{value}%"]})
df_subtitle = pd.DataFrame({"x": [0], "y": [-0.40], "label": ["Sales Performance Score"]})
df_min_max = pd.DataFrame({"x": [-1.08, 1.08], "y": [-0.08, -0.08], "label": [str(min_value), str(max_value)]})

zone_label_radius = 0.73
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

plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", fill="zone", group="zone"), data=df_polygons, color=PAGE_BG, size=0.75, alpha=0.92)
    + scale_fill_manual(values=zone_colors_map)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_needle, color=INK, size=2.5)
    + geom_polygon(aes(x="x", y="y"), data=df_circle, fill=INK, color=INK)
    + geom_text(aes(x="x", y="y", label="label"), data=df_label, size=14, color=INK, fontface="bold")
    + geom_text(aes(x="x", y="y", label="label"), data=df_subtitle, size=7, color=INK_MUTED)
    + geom_text(aes(x="x", y="y", label="label"), data=df_min_max, size=7, color=INK_SOFT)
    + geom_text(aes(x="x", y="y", label="label"), data=df_zone_labels, size=7, color=INK_SOFT, fontface="bold")
    + labs(title="gauge-basic · python · letsplot · anyplot.ai")
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
        plot_title=element_text(size=16, face="bold", color=INK),
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
