""" anyplot.ai
sunburst-basic: Basic Sunburst Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-04
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
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

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


def create_wedge(inner_r, outer_r, start_angle, end_angle, n_points=30):
    angles_outer = [start_angle + (end_angle - start_angle) * i / n_points for i in range(n_points + 1)]
    angles_inner = angles_outer[::-1]
    x_outer = [outer_r * math.cos(a) for a in angles_outer]
    y_outer = [outer_r * math.sin(a) for a in angles_outer]
    x_inner = [inner_r * math.cos(a) for a in angles_inner]
    y_inner = [inner_r * math.sin(a) for a in angles_inner]
    return x_outer + x_inner, y_outer + y_inner


# Okabe-Ito branch colors for level 1; graduated lighter shades for levels 2-3
branch_colors = {
    "Eng": "#009E73",  # Okabe-Ito position 1 — brand green
    "Sales": "#D55E00",  # Okabe-Ito position 2 — vermillion
    "Mktg": "#0072B2",  # Okabe-Ito position 3 — blue
}
level2_colors = {
    "Backend": "#66C5AB",  # Eng, ~40% lighter
    "Frontend": "#80CFB9",  # Eng, ~50% lighter
    "North": "#E69E66",  # Sales, ~40% lighter
    "South": "#EEAF80",  # Sales, ~50% lighter
    "Digital": "#66AAD1",  # Mktg, ~40% lighter
    "Brand": "#80B9D9",  # Mktg, ~50% lighter
}
level3_colors = {
    "API": "#A6DDCE",  # Eng, ~65% lighter
    "Database": "#B3E2D5",  # Eng, ~70% lighter
    "Web App": "#BFE7DC",  # Eng, ~75% lighter
    "Mobile": "#CCECE3",  # Eng, ~80% lighter
    "Enterprise": "#F0C7A6",  # Sales, ~65% lighter
    "SMB": "#F2CFB3",  # Sales, ~70% lighter
    "Retail": "#F5D7BF",  # Sales, ~75% lighter
    "SEO": "#A6CEE4",  # Mktg, ~65% lighter
    "Ads": "#B3D5E8",  # Mktg, ~70% lighter
    "Events": "#BFDCEC",  # Mktg, ~75% lighter
}
all_colors = {**branch_colors, **level2_colors, **level3_colors}

# Ring radii
r_inner_1, r_outer_1 = 0, 28  # Level 1 (innermost, filled center)
r_inner_2, r_outer_2 = 31, 52  # Level 2
r_inner_3, r_outer_3 = 55, 80  # Level 3 (outermost)

# Calculate proportions
level1_agg = df.groupby("level_1")["value"].sum().reset_index()
level1_agg["pct"] = level1_agg["value"] / total_value
level1_agg = level1_agg.sort_values("level_1").reset_index(drop=True)

level2_agg = df.groupby(["level_1", "level_2"])["value"].sum().reset_index()
level2_agg["pct"] = level2_agg["value"] / total_value

df["pct"] = df["value"] / total_value

# Build polygon and label data
polygon_rows = []
label_rows = []
segment_id = 0

start_angle = math.pi / 2  # Start at top, go clockwise
level1_angles = {}

for _, row in level1_agg.iterrows():
    end_angle = start_angle - row["pct"] * 2 * math.pi
    level1_angles[row["level_1"]] = {"start": start_angle, "end": end_angle}

    x_pts, y_pts = create_wedge(r_inner_1, r_outer_1, end_angle, start_angle)
    for x, y in zip(x_pts, y_pts, strict=True):
        polygon_rows.append({"x": x, "y": y, "segment_id": segment_id, "color": row["level_1"]})

    mid_angle = (start_angle + end_angle) / 2
    label_r = r_outer_1 * 0.55
    label_rows.append(
        {"x": label_r * math.cos(mid_angle), "y": label_r * math.sin(mid_angle), "label": row["level_1"], "level": 1}
    )

    segment_id += 1
    start_angle = end_angle

level2_angles = {}

for level1_name in level1_agg["level_1"]:
    l1_angles = level1_angles[level1_name]
    l2_data = level2_agg[level2_agg["level_1"] == level1_name].sort_values("level_2")
    cur_angle = l1_angles["start"]

    for _, row in l2_data.iterrows():
        end_angle = cur_angle - row["pct"] * 2 * math.pi
        level2_angles[(row["level_1"], row["level_2"])] = {"start": cur_angle, "end": end_angle}

        x_pts, y_pts = create_wedge(r_inner_2, r_outer_2, end_angle, cur_angle)
        for x, y in zip(x_pts, y_pts, strict=True):
            polygon_rows.append({"x": x, "y": y, "segment_id": segment_id, "color": row["level_2"]})

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
            for x, y in zip(x_pts, y_pts, strict=True):
                polygon_rows.append({"x": x, "y": y, "segment_id": segment_id, "color": row["level_3"]})

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

# Plot
plot = (
    ggplot(polygon_df)
    + geom_polygon(aes(x="x", y="y", fill="color", group="segment_id"), color=PAGE_BG, size=1.5, alpha=0.9)
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=label_df[label_df["level"] == 1],
        size=12,
        color="#FFFFFF",
        fontface="bold",
    )
    + geom_text(aes(x="x", y="y", label="label"), data=label_df[label_df["level"] == 2], size=11, color="#1A1A17")
    + geom_text(aes(x="x", y="y", label="label"), data=label_df[label_df["level"] == 3], size=9, color="#1A1A17")
    + scale_fill_manual(values=all_colors)
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-100, 100))
    + scale_y_continuous(limits=(-100, 100))
    + labs(title="sunburst-basic · letsplot · anyplot.ai")
    + ggsize(1200, 1200)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=24, hjust=0.5, color=INK),
        legend_position="none",
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
