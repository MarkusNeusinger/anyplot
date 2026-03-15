""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_rect,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_reverse,
    theme,
    theme_minimal,
)


# Data - synthetic sedimentary borehole section
layers = pd.DataFrame(
    {
        "top": [0, 12, 28, 45, 58, 72, 95, 115, 138, 160],
        "bottom": [12, 28, 45, 58, 72, 95, 115, 138, 160, 180],
        "lithology": [
            "Sandstone",
            "Shale",
            "Limestone",
            "Siltstone",
            "Sandstone",
            "Conglomerate",
            "Shale",
            "Limestone",
            "Mudstone",
            "Sandstone",
        ],
        "formation": [
            "Frontier Fm",
            "Frontier Fm",
            "Madison Fm",
            "Madison Fm",
            "Kootenai Fm",
            "Kootenai Fm",
            "Morrison Fm",
            "Morrison Fm",
            "Sundance Fm",
            "Sundance Fm",
        ],
        "age": [
            "Late Cretaceous",
            "Late Cretaceous",
            "Early Cretaceous",
            "Early Cretaceous",
            "Late Jurassic",
            "Late Jurassic",
            "Middle Jurassic",
            "Middle Jurassic",
            "Triassic",
            "Triassic",
        ],
    }
)

layers["mid"] = (layers["top"] + layers["bottom"]) / 2
layers["thickness"] = layers["bottom"] - layers["top"]

# Column position constants
col_left = 0.0
col_right = 4.0
col_mid = 2.0

# Lithology colors (geologically conventional tones)
lith_colors = {
    "Sandstone": "#F5D76E",
    "Shale": "#8E8E8E",
    "Limestone": "#6DAEDB",
    "Siltstone": "#B5C7D3",
    "Conglomerate": "#D4785C",
    "Mudstone": "#7B6B5E",
}

# Build rectangle data for the column
rect_df = layers.copy()
rect_df["xmin"] = col_left
rect_df["xmax"] = col_right
rect_df["ymin"] = rect_df["top"]
rect_df["ymax"] = rect_df["bottom"]

# Generate pattern overlay data for each lithology
pattern_rows = []
np.random.seed(42)

for _, row in layers.iterrows():
    top_val = row["top"]
    bot_val = row["bottom"]
    lith = row["lithology"]
    thickness = bot_val - top_val

    if lith == "Sandstone":
        # Stipple dots pattern
        n_dots = int(thickness * 3)
        for _ in range(n_dots):
            px = np.random.uniform(col_left + 0.3, col_right - 0.3)
            py = np.random.uniform(top_val + 0.5, bot_val - 0.5)
            pattern_rows.append({"x": px, "y": py, "xend": px, "yend": py, "ptype": "dot", "lithology": lith})

    elif lith == "Shale":
        # Horizontal dashes
        spacing = 3.0
        y_pos = top_val + 1.5
        while y_pos < bot_val - 1.0:
            for x_start in np.arange(col_left + 0.3, col_right - 0.5, 0.8):
                pattern_rows.append(
                    {"x": x_start, "y": y_pos, "xend": x_start + 0.5, "yend": y_pos, "ptype": "dash", "lithology": lith}
                )
            y_pos += spacing

    elif lith == "Limestone":
        # Brick pattern: horizontal lines with offset verticals
        spacing = 4.0
        y_pos = top_val + 2.0
        row_idx = 0
        while y_pos < bot_val - 1.0:
            # Horizontal line
            pattern_rows.append(
                {
                    "x": col_left + 0.2,
                    "y": y_pos,
                    "xend": col_right - 0.2,
                    "yend": y_pos,
                    "ptype": "brick_h",
                    "lithology": lith,
                }
            )
            # Vertical lines (offset every other row)
            offset = 1.0 if row_idx % 2 == 0 else 0.0
            for vx in np.arange(col_left + 0.5 + offset, col_right - 0.3, 2.0):
                y_top = max(y_pos - spacing, top_val + 0.2)
                pattern_rows.append(
                    {"x": vx, "y": y_top, "xend": vx, "yend": y_pos, "ptype": "brick_v", "lithology": lith}
                )
            y_pos += spacing
            row_idx += 1

    elif lith == "Siltstone":
        # Short random dashes at various angles
        n_dashes = int(thickness * 2)
        for _ in range(n_dashes):
            px = np.random.uniform(col_left + 0.4, col_right - 0.4)
            py = np.random.uniform(top_val + 1.0, bot_val - 1.0)
            dx = np.random.uniform(-0.2, 0.2)
            pattern_rows.append(
                {"x": px, "y": py, "xend": px + dx, "yend": py + 0.3, "ptype": "short_dash", "lithology": lith}
            )

    elif lith == "Conglomerate":
        # Scattered circles (represented as large dots)
        n_circles = int(thickness * 1.5)
        for _ in range(n_circles):
            px = np.random.uniform(col_left + 0.5, col_right - 0.5)
            py = np.random.uniform(top_val + 1.0, bot_val - 1.0)
            pattern_rows.append({"x": px, "y": py, "xend": px, "yend": py, "ptype": "circle", "lithology": lith})

    elif lith == "Mudstone":
        # Dense horizontal dashes (finer than shale)
        spacing = 2.5
        y_pos = top_val + 1.0
        while y_pos < bot_val - 0.5:
            for x_start in np.arange(col_left + 0.2, col_right - 0.3, 0.6):
                pattern_rows.append(
                    {
                        "x": x_start,
                        "y": y_pos,
                        "xend": x_start + 0.3,
                        "yend": y_pos,
                        "ptype": "fine_dash",
                        "lithology": lith,
                    }
                )
            y_pos += spacing

pattern_df = pd.DataFrame(pattern_rows)

# Separate pattern types for layered rendering
dots_df = pattern_df[pattern_df["ptype"] == "dot"].copy()
circles_df = pattern_df[pattern_df["ptype"] == "circle"].copy()
lines_df = pattern_df[pattern_df["ptype"].isin(["dash", "brick_h", "brick_v", "short_dash", "fine_dash"])].copy()

# Formation label data (one label per formation, positioned at midpoint)
form_groups = layers.groupby("formation", sort=False).agg({"top": "min", "bottom": "max"})
form_groups["mid"] = (form_groups["top"] + form_groups["bottom"]) / 2
form_labels = pd.DataFrame({"x": col_right + 0.3, "y": form_groups["mid"].values, "label": form_groups.index.tolist()})

# Age label data (one label per age, positioned at midpoint)
age_groups = layers.groupby("age", sort=False).agg({"top": "min", "bottom": "max"})
age_groups["mid"] = (age_groups["top"] + age_groups["bottom"]) / 2
age_labels = pd.DataFrame({"x": col_left - 0.3, "y": age_groups["mid"].values, "label": age_groups.index.tolist()})

# Layer boundary lines
boundaries = sorted(set(layers["top"].tolist() + layers["bottom"].tolist()))
boundary_df = pd.DataFrame(
    {"x": [col_left] * len(boundaries), "xend": [col_right] * len(boundaries), "y": boundaries, "yend": boundaries}
)

# Plot
plot = (
    ggplot()
    # Colored rectangles for each layer
    + geom_rect(
        data=rect_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="lithology"),
        color="#2C2C2C",
        size=0.8,
        alpha=0.55,
    )
    # Pattern overlays - line segments
    + geom_segment(
        data=lines_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#2C2C2C", size=0.6, alpha=0.7
    )
    # Pattern overlays - dots (sandstone)
    + geom_point(data=dots_df, mapping=aes(x="x", y="y"), color="#2C2C2C", size=0.8, alpha=0.6)
    # Pattern overlays - circles (conglomerate)
    + geom_point(
        data=circles_df,
        mapping=aes(x="x", y="y"),
        color="#2C2C2C",
        size=3,
        alpha=0.5,
        shape="o",
        fill="none",
        stroke=0.8,
    )
    # Layer boundary lines
    + geom_segment(data=boundary_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#2C2C2C", size=0.8)
    # Formation labels (right side)
    + geom_text(
        data=form_labels,
        mapping=aes(x="x", y="y", label="label"),
        ha="left",
        size=11,
        fontstyle="italic",
        color="#1A1A1A",
    )
    # Age labels (left side)
    + geom_text(data=age_labels, mapping=aes(x="x", y="y", label="label"), ha="right", size=10, color="#1A1A1A")
    # Scales
    + scale_fill_manual(values=lith_colors)
    + scale_y_reverse(name="Depth (m)", breaks=list(range(0, 200, 20)))
    + scale_x_continuous(limits=(-3.5, 8.5), breaks=[])
    # Labels
    + labs(title="column-stratigraphic · plotnine · pyplots.ai", fill="Lithology", x="")
    # Theme
    + theme_minimal()
    + theme(
        figure_size=(10, 16),
        plot_title=element_text(size=22, face="bold", ha="center"),
        axis_title_y=element_text(size=18),
        axis_title_x=element_blank(),
        axis_text_y=element_text(size=14),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=13),
        legend_position="bottom",
        legend_direction="horizontal",
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3, alpha=0.4),
        panel_grid_minor_y=element_blank(),
        panel_background=element_rect(fill="white", color="none"),
        plot_background=element_rect(fill="white", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, width=10, height=16)
