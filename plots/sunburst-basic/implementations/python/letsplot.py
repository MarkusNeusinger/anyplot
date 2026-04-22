""" pyplots.ai
sunburst-basic: Basic Sunburst Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
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

# Data - Organizational budget by department, team, and project (3 levels)
data = [
    # Engineering branch
    {"level_1": "Eng", "level_2": "Backend", "level_3": "API", "value": 15},
    {"level_1": "Eng", "level_2": "Backend", "level_3": "Database", "value": 10},
    {"level_1": "Eng", "level_2": "Frontend", "level_3": "Web App", "value": 12},
    {"level_1": "Eng", "level_2": "Frontend", "level_3": "Mobile", "value": 8},
    # Sales branch
    {"level_1": "Sales", "level_2": "North", "level_3": "Enterprise", "value": 18},
    {"level_1": "Sales", "level_2": "North", "level_3": "SMB", "value": 7},
    {"level_1": "Sales", "level_2": "South", "level_3": "Retail", "value": 9},
    # Marketing branch
    {"level_1": "Mktg", "level_2": "Digital", "level_3": "SEO", "value": 6},
    {"level_1": "Mktg", "level_2": "Digital", "level_3": "Ads", "value": 8},
    {"level_1": "Mktg", "level_2": "Brand", "level_3": "Events", "value": 7},
]

df = pd.DataFrame(data)
total_value = df["value"].sum()


# Create arc/wedge polygon points
def create_wedge(inner_r, outer_r, start_angle, end_angle, n_points=30):
    """Create polygon points for a wedge (arc segment)."""
    angles_outer = [start_angle + (end_angle - start_angle) * i / n_points for i in range(n_points + 1)]
    angles_inner = angles_outer[::-1]

    x_outer = [outer_r * math.cos(a) for a in angles_outer]
    y_outer = [outer_r * math.sin(a) for a in angles_outer]
    x_inner = [inner_r * math.cos(a) for a in angles_inner]
    y_inner = [inner_r * math.sin(a) for a in angles_inner]

    return x_outer + x_inner, y_outer + y_inner


# Define colors for level 1 categories (branch colors)
branch_colors = {
    "Eng": "#306998",  # Python Blue
    "Sales": "#FFD43B",  # Python Yellow
    "Mktg": "#4CAF50",  # Green
}

# Lighter shades for level 2
level2_colors = {
    "Backend": "#4A8BBF",
    "Frontend": "#6BA3D0",
    "North": "#FFE066",
    "South": "#FFEB99",
    "Digital": "#66BB6A",
    "Brand": "#81C784",
}

# Even lighter shades for level 3
level3_colors = {
    "API": "#7AAFDC",
    "Database": "#8BBDE4",
    "Web App": "#9CCBEC",
    "Mobile": "#ADD9F4",
    "Enterprise": "#FFF099",
    "SMB": "#FFF5B3",
    "Retail": "#FFF9CC",
    "SEO": "#A5D6A7",
    "Ads": "#B8E0B9",
    "Events": "#C8E6C9",
}

# Ring radii (filled center, no center hole)
r_inner_1, r_outer_1 = 0, 28  # Level 1 (innermost, filled center)
r_inner_2, r_outer_2 = 31, 52  # Level 2
r_inner_3, r_outer_3 = 55, 80  # Level 3 (outermost)

# Calculate angles for each level
level1_agg = df.groupby("level_1")["value"].sum().reset_index()
level1_agg["pct"] = level1_agg["value"] / total_value
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

for _, row in level1_agg.iterrows():
    end_angle = start_angle - row["pct"] * 2 * math.pi  # Clockwise
    level1_angles[row["level_1"]] = {"start": start_angle, "end": end_angle}

    x_pts, y_pts = create_wedge(r_inner_1, r_outer_1, end_angle, start_angle)
    for x, y in zip(x_pts, y_pts, strict=True):
        polygon_rows.append(
            {"x": x, "y": y, "segment_id": segment_id, "level": 1, "label": row["level_1"], "color": row["level_1"]}
        )

    mid_angle = (start_angle + end_angle) / 2
    # Place label in middle of the filled pie slice
    label_r = r_outer_1 * 0.55
    label_rows.append(
        {"x": label_r * math.cos(mid_angle), "y": label_r * math.sin(mid_angle), "label": row["level_1"], "level": 1}
    )

    segment_id += 1
    start_angle = end_angle

# Track angles for level 2
level2_angles = {}

for level1_name in level1_agg["level_1"]:
    l1_angles = level1_angles[level1_name]
    l2_data = level2_agg[level2_agg["level_1"] == level1_name].sort_values("level_2")

    cur_angle = l1_angles["start"]

    for _, row in l2_data.iterrows():
        end_angle = cur_angle - row["pct"] * 2 * math.pi
        level2_angles[(row["level_1"], row["level_2"])] = {"start": cur_angle, "end": end_angle}

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
            }
        )

        segment_id += 1
        cur_angle = end_angle

# Level 3 segments
for level1_name in level1_agg["level_1"]:
    l2_data = level2_agg[level2_agg["level_1"] == level1_name].sort_values("level_2")

    for _, l2_row in l2_data.iterrows():
        l2_key = (l2_row["level_1"], l2_row["level_2"])
        l2_angles_range = level2_angles[l2_key]

        l3_data = df[(df["level_1"] == l2_row["level_1"]) & (df["level_2"] == l2_row["level_2"])].sort_values("level_3")

        cur_angle = l2_angles_range["start"]

        for _, row in l3_data.iterrows():
            end_angle = cur_angle - row["pct"] * 2 * math.pi

            x_pts, y_pts = create_wedge(r_inner_3, r_outer_3, end_angle, cur_angle)
            color_key = row["level_3"]
            for x, y in zip(x_pts, y_pts, strict=True):
                polygon_rows.append(
                    {"x": x, "y": y, "segment_id": segment_id, "level": 3, "label": row["level_3"], "color": color_key}
                )

            mid_angle = (cur_angle + end_angle) / 2
            label_r = (r_inner_3 + r_outer_3) / 2
            label_rows.append(
                {
                    "x": label_r * math.cos(mid_angle),
                    "y": label_r * math.sin(mid_angle),
                    "label": row["level_3"],
                    "level": 3,
                }
            )

            segment_id += 1
            cur_angle = end_angle

polygon_df = pd.DataFrame(polygon_rows)
label_df = pd.DataFrame(label_rows)

# Build color mapping combining all levels
all_colors = {}
all_colors.update(branch_colors)
all_colors.update(level2_colors)
all_colors.update(level3_colors)

unique_colors = polygon_df["color"].unique()
color_values = [all_colors.get(c, "#888888") for c in unique_colors]

# Plot
plot = (
    ggplot(polygon_df)
    + geom_polygon(aes(x="x", y="y", fill="color", group="segment_id"), color="white", size=1.5, alpha=0.9)
    + geom_text(
        aes(x="x", y="y", label="label"), data=label_df[label_df["level"] == 1], size=12, color="white", fontface="bold"
    )
    + geom_text(aes(x="x", y="y", label="label"), data=label_df[label_df["level"] == 2], size=11, color="#333333")
    + geom_text(aes(x="x", y="y", label="label"), data=label_df[label_df["level"] == 3], size=9, color="#333333")
    + scale_fill_manual(values=color_values)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-100, 100))
    + scale_y_continuous(limits=(-100, 100))
    + labs(title="sunburst-basic · letsplot · pyplots.ai")
    + ggsize(1200, 1200)  # Square format for radial chart
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
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
