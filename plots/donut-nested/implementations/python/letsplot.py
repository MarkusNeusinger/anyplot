""" pyplots.ai
donut-nested: Nested Donut Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import math

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
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


# Create arc/wedge polygon points for donut segments
def create_wedge(inner_r, outer_r, start_angle, end_angle, n_points=40):
    """Create polygon points for a wedge (arc segment)."""
    angles_outer = [start_angle + (end_angle - start_angle) * i / n_points for i in range(n_points + 1)]
    angles_inner = angles_outer[::-1]

    x_outer = [outer_r * math.cos(a) for a in angles_outer]
    y_outer = [outer_r * math.sin(a) for a in angles_outer]
    x_inner = [inner_r * math.cos(a) for a in angles_inner]
    y_inner = [inner_r * math.sin(a) for a in angles_inner]

    return x_outer + x_inner, y_outer + y_inner


# Define colors for level 1 categories (parent categories - inner ring)
parent_colors = {
    "Marketing": "#306998",  # Python Blue
    "Operations": "#FFD43B",  # Python Yellow
    "R&D": "#4CAF50",  # Green
    "Sales": "#FF7043",  # Orange
}

# Lighter shades for level 2 (children - outer ring)
# Using consistent color families per parent
child_colors = {
    # Marketing family (blues)
    "Advertising": "#4A8BBF",
    "Events": "#6BA3D0",
    "Content": "#8CBDE3",
    # Operations family (yellows)
    "Facilities": "#FFE066",
    "IT Support": "#FFEB99",
    "Logistics": "#FFF5CC",
    # R&D family (greens)
    "Product Dev": "#66BB6A",
    "Research": "#81C784",
    # Sales family (oranges)
    "Field Sales": "#FF9066",
    "Inside Sales": "#FFAB91",
}

# Ring radii (donut with center hole)
r_inner_1, r_outer_1 = 25, 50  # Level 1 (inner ring)
r_inner_2, r_outer_2 = 55, 85  # Level 2 (outer ring)

# Calculate angles for each level
level1_agg = df.groupby("level_1")["value"].sum().reset_index()
level1_agg["pct"] = level1_agg["value"] / total_value
# Define custom order for level 1
level1_order = ["Marketing", "Operations", "R&D", "Sales"]
level1_agg["level_1"] = pd.Categorical(level1_agg["level_1"], categories=level1_order, ordered=True)
level1_agg = level1_agg.sort_values("level_1").reset_index(drop=True)

level2_agg = df.groupby(["level_1", "level_2"])["value"].sum().reset_index()
level2_agg["pct"] = level2_agg["value"] / total_value

df["pct"] = df["value"] / total_value

# Build polygon data for each segment
polygon_rows = []
label_rows = []
segment_id = 0

# Start angle at top (90 degrees = pi/2)
start_angle = math.pi / 2

# Track angles for level 1
level1_angles = {}

# Create inner ring segments (level 1 - parent categories)
for _, row in level1_agg.iterrows():
    end_angle = start_angle - row["pct"] * 2 * math.pi  # Clockwise

    level1_angles[row["level_1"]] = {"start": start_angle, "end": end_angle}

    x_pts, y_pts = create_wedge(r_inner_1, r_outer_1, end_angle, start_angle)
    for x, y in zip(x_pts, y_pts, strict=True):
        polygon_rows.append(
            {"x": x, "y": y, "segment_id": segment_id, "level": 1, "label": row["level_1"], "color": row["level_1"]}
        )

    # Position label in middle of the arc
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

# Create outer ring segments (level 2 - child categories)
for level1_name in level1_order:
    if level1_name not in level1_angles:
        continue
    l1_angles = level1_angles[level1_name]
    l2_data = level2_agg[level2_agg["level_1"] == level1_name].sort_values("level_2")

    cur_angle = l1_angles["start"]

    for _, row in l2_data.iterrows():
        end_angle = cur_angle - row["pct"] * 2 * math.pi

        x_pts, y_pts = create_wedge(r_inner_2, r_outer_2, end_angle, cur_angle)
        color_key = row["level_2"]
        for x, y in zip(x_pts, y_pts, strict=True):
            polygon_rows.append(
                {"x": x, "y": y, "segment_id": segment_id, "level": 2, "label": row["level_2"], "color": color_key}
            )

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

# Build color mapping combining all levels
all_colors = {}
all_colors.update(parent_colors)
all_colors.update(child_colors)

unique_colors = polygon_df["color"].unique()
color_values = [all_colors.get(c, "#888888") for c in unique_colors]

# Create center label for total
center_df = pd.DataFrame({"x": [0.0], "y": [0.0], "label": [f"Total\n${total_value}M"]})

# Plot
plot = (
    ggplot(polygon_df)
    + geom_polygon(aes(x="x", y="y", fill="color", group="segment_id"), color="white", size=2.0, alpha=0.95)
    # Inner ring labels (parent categories)
    + geom_text(
        aes(x="x", y="y", label="label"), data=label_df[label_df["level"] == 1], size=11, color="white", fontface="bold"
    )
    # Outer ring labels (child categories)
    + geom_text(aes(x="x", y="y", label="label"), data=label_df[label_df["level"] == 2], size=9, color="#333333")
    # Center label
    + geom_text(aes(x="x", y="y", label="label"), data=center_df, size=14, color="#333333", fontface="bold")
    + scale_fill_manual(values=color_values)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-110, 110))
    + scale_y_continuous(limits=(-110, 110))
    + labs(title="donut-nested · letsplot · pyplots.ai")
    + ggsize(1200, 1200)  # Square format for radial chart
    + theme(
        plot_title=element_text(size=26, hjust=0.5),
        legend_position="none",
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
