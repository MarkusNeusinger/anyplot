""" pyplots.ai
column-stratigraphic: Stratigraphic Column with Lithology Patterns
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-15
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_label,
    geom_linerange,
    geom_point,
    geom_segment,
    geom_text,
    geom_tile,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - synthetic sedimentary borehole section (Western US)
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

# Derived columns for grammar-of-graphics mapping
layers["mid"] = (layers["top"] + layers["bottom"]) / 2
layers["thickness"] = layers["bottom"] - layers["top"]
layers["x_center"] = 2.0

# Column position constants
col_left = 0.0
col_right = 4.0

# Lithology colors - enhanced contrast, colorblind-friendly palette
lith_colors = {
    "Sandstone": "#EEC946",
    "Shale": "#B0B0B0",
    "Limestone": "#5A9BD5",
    "Siltstone": "#7EBF8E",
    "Conglomerate": "#D4785C",
    "Mudstone": "#8B6914",
}

# Unconformity depth (J/K boundary between Kootenai Fm and Morrison Fm)
unconformity_depth = 95.0

# Generate pattern overlay data with helper functions to reduce verbosity
np.random.seed(42)
pattern_rows = []


def _add_random_points(rows, top_val, bot_val, lith, n, ptype, x_pad=0.3, y_pad=0.5):
    xs = np.random.uniform(col_left + x_pad, col_right - x_pad, n)
    ys = np.random.uniform(top_val + y_pad, bot_val - y_pad, n)
    for px, py in zip(xs, ys, strict=True):
        rows.append({"x": px, "y": py, "xend": px, "yend": py, "ptype": ptype, "lithology": lith})


def _add_horiz_dashes(rows, top_val, bot_val, lith, spacing, ptype, dash_len=0.5, x_step=0.8):
    y_pos = top_val + spacing * 0.4
    while y_pos < bot_val - 0.3:
        for x_start in np.arange(col_left + 0.3, col_right - 0.3, x_step):
            rows.append(
                {"x": x_start, "y": y_pos, "xend": x_start + dash_len, "yend": y_pos, "ptype": ptype, "lithology": lith}
            )
        y_pos += spacing


for _, row in layers.iterrows():
    top_val, bot_val, lith = row["top"], row["bottom"], row["lithology"]
    thickness = bot_val - top_val

    if lith == "Sandstone":
        _add_random_points(pattern_rows, top_val, bot_val, lith, int(thickness * 5), "dot")

    elif lith == "Shale":
        _add_horiz_dashes(pattern_rows, top_val, bot_val, lith, spacing=2.5, ptype="dash", dash_len=0.5, x_step=0.8)

    elif lith == "Limestone":
        spacing = 4.0
        y_pos = top_val + 2.0
        row_idx = 0
        while y_pos < bot_val - 1.0:
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
            offset = 1.0 if row_idx % 2 == 0 else 0.0
            for vx in np.arange(col_left + 0.5 + offset, col_right - 0.3, 2.0):
                y_top = max(y_pos - spacing, top_val + 0.2)
                pattern_rows.append(
                    {"x": vx, "y": y_top, "xend": vx, "yend": y_pos, "ptype": "brick_v", "lithology": lith}
                )
            y_pos += spacing
            row_idx += 1

    elif lith == "Siltstone":
        n_dashes = int(thickness * 8)
        xs = np.random.uniform(col_left + 0.3, col_right - 0.3, n_dashes)
        ys = np.random.uniform(top_val + 0.5, bot_val - 0.5, n_dashes)
        dxs = np.random.uniform(-0.2, 0.2, n_dashes)
        for px, py, dx in zip(xs, ys, dxs, strict=True):
            pattern_rows.append(
                {"x": px, "y": py, "xend": px + dx, "yend": py + 0.3, "ptype": "short_dash", "lithology": lith}
            )

    elif lith == "Conglomerate":
        _add_random_points(pattern_rows, top_val, bot_val, lith, int(thickness * 2.5), "circle", x_pad=0.5, y_pad=1.0)

    elif lith == "Mudstone":
        _add_horiz_dashes(
            pattern_rows, top_val, bot_val, lith, spacing=1.8, ptype="fine_dash", dash_len=0.25, x_step=0.5
        )

pattern_df = pd.DataFrame(pattern_rows)

# Separate pattern types for layered rendering
dots_df = pattern_df[pattern_df["ptype"] == "dot"].copy()
circles_df = pattern_df[pattern_df["ptype"] == "circle"].copy()
lines_df = pattern_df[pattern_df["ptype"].isin(["dash", "brick_h", "brick_v", "short_dash", "fine_dash"])].copy()

# Formation label data (one per formation at midpoint) using grammar groupby
form_groups = layers.groupby("formation", sort=False).agg({"top": "min", "bottom": "max"}).reset_index()
form_groups["mid"] = (form_groups["top"] + form_groups["bottom"]) / 2
form_groups["x"] = col_right + 0.4

# Age label data (one per age at midpoint)
age_groups = layers.groupby("age", sort=False).agg({"top": "min", "bottom": "max"}).reset_index()
age_groups["mid"] = (age_groups["top"] + age_groups["bottom"]) / 2
age_groups["x"] = col_left - 0.6
age_groups["ymin"] = age_groups["top"] + 0.5
age_groups["ymax"] = age_groups["bottom"] - 0.5
age_groups["bracket_x"] = col_left - 0.2

# Boundary depths for horizontal lines
boundaries = sorted(set(layers["top"].tolist() + layers["bottom"].tolist()))
boundary_df = pd.DataFrame(
    {"x": [col_left] * len(boundaries), "xend": [col_right] * len(boundaries), "y": boundaries, "yend": boundaries}
)

# Unconformity wavy line data
wavy_x = np.linspace(col_left - 0.15, col_right + 0.15, 45)
wavy_y = unconformity_depth + np.sin(wavy_x * 8) * 0.8
wavy_df = pd.DataFrame({"x": wavy_x[:-1], "y": wavy_y[:-1], "xend": wavy_x[1:], "yend": wavy_y[1:]})

# Build plot using plotnine grammar of graphics
plot = (
    ggplot()
    # Layer fills using geom_tile with grammar-driven aesthetic mapping
    + geom_tile(
        data=layers,
        mapping=aes(x="x_center", y="mid", width=col_right - col_left, height="thickness", fill="lithology"),
        color="#3A3A3A",
        size=0.9,
        alpha=0.7,
    )
    # Pattern overlays - line segments (thicker for visibility)
    + geom_segment(
        data=lines_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#2C2C2C", size=0.65, alpha=0.8
    )
    # Pattern overlays - stipple dots (sandstone)
    + geom_point(data=dots_df, mapping=aes(x="x", y="y"), color="#2C2C2C", size=1.2, alpha=0.7)
    # Pattern overlays - open circles (conglomerate)
    + geom_point(
        data=circles_df,
        mapping=aes(x="x", y="y"),
        color="#2C2C2C",
        size=3.5,
        alpha=0.6,
        shape="o",
        fill="none",
        stroke=0.9,
    )
    # Layer boundary lines
    + geom_segment(data=boundary_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#3A3A3A", size=0.9)
    # Unconformity wavy line (firebrick red - focal point for data storytelling)
    + geom_segment(
        data=wavy_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#B22222", size=2.2, alpha=0.95
    )
    # Unconformity annotation
    + annotate(
        "text",
        x=col_right + 0.4,
        y=unconformity_depth,
        label="~ Unconformity ~",
        ha="left",
        size=15,
        color="#B22222",
        fontstyle="italic",
        fontweight="bold",
    )
    # Age bracket lines using geom_linerange (idiomatic plotnine for vertical ranges)
    + geom_linerange(data=age_groups, mapping=aes(x="bracket_x", ymin="ymin", ymax="ymax"), color="#444444", size=0.9)
    # Formation labels using geom_label (plotnine-native styled text with background)
    + geom_label(
        data=form_groups,
        mapping=aes(x="x", y="mid", label="formation"),
        ha="left",
        size=17,
        fontstyle="italic",
        color="#1A1A1A",
        fill="#FFFFFFCC",
        label_padding=0.3,
        label_size=0.3,
    )
    # Age labels (left side) - increased size for legibility
    + geom_text(
        data=age_groups,
        mapping=aes(x="x", y="mid", label="age"),
        ha="right",
        size=17,
        fontweight="bold",
        color="#2A2A2A",
    )
    # Scales - grammar-driven fill mapping with manual color values
    + scale_fill_manual(values=lith_colors, name="Lithology")
    + scale_x_continuous(limits=(-4.0, 8.5), breaks=[])
    + scale_y_continuous(trans="reverse", name="Depth (m)", breaks=list(range(0, 200, 20)))
    # Clipping for clean edges
    + coord_cartesian(ylim=(185, -5))
    # Labels
    + labs(title="column-stratigraphic · plotnine · pyplots.ai", x="")
    # Legend configuration
    + guides(fill=guide_legend(nrow=1))
    # Theme - extensive plotnine theme customization
    + theme_minimal()
    + theme(
        figure_size=(12, 16),
        plot_title=element_text(size=26, face="bold", ha="center"),
        axis_title_y=element_text(size=22),
        axis_title_x=element_blank(),
        axis_text_y=element_text(size=18, color="#333333"),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        legend_title=element_text(size=18, face="bold"),
        legend_text=element_text(size=16),
        legend_position="bottom",
        legend_direction="horizontal",
        legend_key_size=22,
        legend_background=element_rect(fill="#F5F5F5", color="#CCCCCC", size=0.4),
        legend_margin=10,
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#D8D8D8", size=0.3, alpha=0.35),
        panel_grid_minor_y=element_blank(),
        panel_background=element_rect(fill="#FAFAFA", color="none"),
        plot_background=element_rect(fill="#FFFFFF", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, width=12, height=16)
