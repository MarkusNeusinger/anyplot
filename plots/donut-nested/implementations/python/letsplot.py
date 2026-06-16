""" anyplot.ai
donut-nested: Nested Donut Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-08
"""

import math
import os

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Budget allocation by department (inner) and expense categories (outer)
data = [
    # Marketing department
    {"level_1": "Marketing", "level_2": "Advertising", "value": 18},
    {"level_1": "Marketing", "level_2": "Events", "value": 8},
    {"level_1": "Marketing", "level_2": "Content", "value": 6},
    # Operations department
    {"level_1": "Operations", "level_2": "Facilities", "value": 12},
    {"level_1": "Operations", "level_2": "IT Support", "value": 10},
    {"level_1": "Operations", "level_2": "Logistics", "value": 8},
    # Research & Development
    {"level_1": "R&D", "level_2": "Product Dev", "value": 15},
    {"level_1": "R&D", "level_2": "Research", "value": 10},
    # Sales department
    {"level_1": "Sales", "level_2": "Field Sales", "value": 9},
    {"level_1": "Sales", "level_2": "Inside Sales", "value": 4},
]

df = pd.DataFrame(data)
total_value = df["value"].sum()

# Ring radii
r_inner_1, r_outer_1 = 25, 50
r_inner_2, r_outer_2 = 55, 85

# Calculate percentages and aggregations
level1_agg = df.groupby("level_1")["value"].sum().reset_index()
level1_agg["pct"] = level1_agg["value"] / total_value
level1_order = ["Marketing", "Operations", "R&D", "Sales"]
level1_agg["level_1"] = pd.Categorical(level1_agg["level_1"], categories=level1_order, ordered=True)
level1_agg = level1_agg.sort_values("level_1").reset_index(drop=True)

level2_agg = df.groupby(["level_1", "level_2"])["value"].sum().reset_index()
level2_agg["pct"] = level2_agg["value"] / total_value

# Map categories to colors
color_map_l1 = {cat: IMPRINT[i] for i, cat in enumerate(level1_order)}
color_map_l2 = {}
for l1_cat in level1_order:
    children = level2_agg[level2_agg["level_1"] == l1_cat]["level_2"].unique()
    parent_color = color_map_l1[l1_cat]
    for child in children:
        color_map_l2[child] = parent_color

# Build polygon data for segments
polygon_rows = []
label_rows = []
segment_id = 0
level1_angles = {}
start_angle = math.pi / 2

# Inner ring (level 1)
for _, row in level1_agg.iterrows():
    end_angle = start_angle - row["pct"] * 2 * math.pi
    level1_angles[row["level_1"]] = {"start": start_angle, "end": end_angle}

    # Create polygon points for this wedge
    angles_outer = [start_angle + (end_angle - start_angle) * i / 40 for i in range(41)]
    angles_inner = angles_outer[::-1]
    x_outer = [r_outer_1 * math.cos(a) for a in angles_outer]
    y_outer = [r_outer_1 * math.sin(a) for a in angles_outer]
    x_inner = [r_inner_1 * math.cos(a) for a in angles_inner]
    y_inner = [r_inner_1 * math.sin(a) for a in angles_inner]
    x_pts, y_pts = x_outer + x_inner, y_outer + y_inner

    for x, y in zip(x_pts, y_pts, strict=False):
        polygon_rows.append(
            {"x": x, "y": y, "segment_id": segment_id, "level": 1, "label": row["level_1"], "color": row["level_1"]}
        )

    # Label for inner ring
    mid_angle = (start_angle + end_angle) / 2
    label_r = (r_inner_1 + r_outer_1) / 2
    label_rows.append(
        {
            "x": label_r * math.cos(mid_angle),
            "y": label_r * math.sin(mid_angle),
            "label": row["level_1"],
            "level": 1,
            "pct": row["pct"] * 100,
        }
    )

    segment_id += 1
    start_angle = end_angle

# Outer ring (level 2)
for level1_name in level1_order:
    if level1_name not in level1_angles:
        continue
    l1_angles = level1_angles[level1_name]
    l2_data = level2_agg[level2_agg["level_1"] == level1_name].sort_values("level_2")

    cur_angle = l1_angles["start"]

    for _, row in l2_data.iterrows():
        end_angle = cur_angle - row["pct"] * 2 * math.pi

        # Create polygon points for this wedge
        angles_outer = [cur_angle + (end_angle - cur_angle) * i / 40 for i in range(41)]
        angles_inner = angles_outer[::-1]
        x_outer = [r_outer_2 * math.cos(a) for a in angles_outer]
        y_outer = [r_outer_2 * math.sin(a) for a in angles_outer]
        x_inner = [r_inner_2 * math.cos(a) for a in angles_inner]
        y_inner = [r_inner_2 * math.sin(a) for a in angles_inner]
        x_pts, y_pts = x_outer + x_inner, y_outer + y_inner

        for x, y in zip(x_pts, y_pts, strict=False):
            polygon_rows.append(
                {"x": x, "y": y, "segment_id": segment_id, "level": 2, "label": row["level_2"], "color": row["level_2"]}
            )

        # Label for outer ring with percentage
        mid_angle = (cur_angle + end_angle) / 2
        label_r = (r_inner_2 + r_outer_2) / 2
        label_rows.append(
            {
                "x": label_r * math.cos(mid_angle),
                "y": label_r * math.sin(mid_angle),
                "label": row["level_2"],
                "level": 2,
                "pct": row["pct"] * 100,
            }
        )

        segment_id += 1
        cur_angle = end_angle

polygon_df = pd.DataFrame(polygon_rows)
label_df = pd.DataFrame(label_rows)

# Build unified color mapping
all_colors = {}
all_colors.update(color_map_l1)
all_colors.update(color_map_l2)
unique_colors = polygon_df["color"].unique()
color_values = [all_colors.get(c, "#888888") for c in unique_colors]

# Center label
center_df = pd.DataFrame({"x": [0.0], "y": [0.0], "label": [f"Total\n${total_value}M"]})

# Theme configuration
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    plot_title=element_text(size=28, color=INK, hjust=0.5),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    panel_grid=element_blank(),
    legend_position="none",
)

# Plot
plot = (
    ggplot(polygon_df)
    + geom_polygon(aes(x="x", y="y", fill="color", group="segment_id"), color=PAGE_BG, size=2.0, alpha=0.95)
    # Inner ring labels (parent categories)
    + geom_text(
        aes(x="x", y="y", label="label"), data=label_df[label_df["level"] == 1], size=12, color=INK, fontface="bold"
    )
    # Outer ring labels (child categories)
    + geom_text(aes(x="x", y="y", label="label"), data=label_df[label_df["level"] == 2], size=10, color=INK_SOFT)
    # Center label
    + geom_text(aes(x="x", y="y", label="label"), data=center_df, size=16, color=INK, fontface="bold")
    + scale_fill_manual(values=color_values)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-110, 110))
    + scale_y_continuous(limits=(-110, 110))
    + labs(title="donut-nested · letsplot · anyplot.ai")
    + ggsize(1200, 1200)
    + anyplot_theme
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
