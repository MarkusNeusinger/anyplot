"""pyplots.ai
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

# Lithology colors - improved contrast (Shale lighter gray, Mudstone warm brown)
lith_colors = {
    "Sandstone": "#F5D76E",
    "Shale": "#A8A8A8",
    "Limestone": "#6DAEDB",
    "Siltstone": "#C8DCC0",
    "Conglomerate": "#D4785C",
    "Mudstone": "#8B6914",
}

# Unconformity depth (J/K boundary between Kootenai Fm and Morrison Fm)
unconformity_depth = 95.0

# Generate pattern overlay data for each lithology
pattern_rows = []
np.random.seed(42)

for _, row in layers.iterrows():
    top_val = row["top"]
    bot_val = row["bottom"]
    lith = row["lithology"]
    thickness = bot_val - top_val

    if lith == "Sandstone":
        n_dots = int(thickness * 4)
        for _ in range(n_dots):
            px = np.random.uniform(col_left + 0.3, col_right - 0.3)
            py = np.random.uniform(top_val + 0.5, bot_val - 0.5)
            pattern_rows.append({"x": px, "y": py, "xend": px, "yend": py, "ptype": "dot", "lithology": lith})

    elif lith == "Shale":
        spacing = 2.5
        y_pos = top_val + 1.0
        while y_pos < bot_val - 0.5:
            for x_start in np.arange(col_left + 0.3, col_right - 0.5, 0.8):
                pattern_rows.append(
                    {"x": x_start, "y": y_pos, "xend": x_start + 0.5, "yend": y_pos, "ptype": "dash", "lithology": lith}
                )
            y_pos += spacing

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
        n_dashes = int(thickness * 6)
        for _ in range(n_dashes):
            px = np.random.uniform(col_left + 0.3, col_right - 0.3)
            py = np.random.uniform(top_val + 0.5, bot_val - 0.5)
            dx = np.random.uniform(-0.15, 0.15)
            pattern_rows.append(
                {"x": px, "y": py, "xend": px + dx, "yend": py + 0.2, "ptype": "short_dash", "lithology": lith}
            )

    elif lith == "Conglomerate":
        n_circles = int(thickness * 2)
        for _ in range(n_circles):
            px = np.random.uniform(col_left + 0.5, col_right - 0.5)
            py = np.random.uniform(top_val + 1.0, bot_val - 1.0)
            pattern_rows.append({"x": px, "y": py, "xend": px, "yend": py, "ptype": "circle", "lithology": lith})

    elif lith == "Mudstone":
        spacing = 2.0
        y_pos = top_val + 0.8
        while y_pos < bot_val - 0.3:
            for x_start in np.arange(col_left + 0.2, col_right - 0.3, 0.5):
                pattern_rows.append(
                    {
                        "x": x_start,
                        "y": y_pos,
                        "xend": x_start + 0.25,
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
wavy_x = np.linspace(col_left, col_right, 40)
wavy_y = unconformity_depth + np.sin(wavy_x * 8) * 0.8
wavy_df = pd.DataFrame({"x": wavy_x[:-1], "y": wavy_y[:-1], "xend": wavy_x[1:], "yend": wavy_y[1:]})

# Build plot using plotnine grammar of graphics
plot = (
    ggplot()
    # Layer fills using geom_tile with grammar-driven aesthetic mapping
    + geom_tile(
        data=layers,
        mapping=aes(x="x_center", y="mid", width=col_right - col_left, height="thickness", fill="lithology"),
        color="#2C2C2C",
        size=0.8,
        alpha=0.6,
    )
    # Pattern overlays - line segments
    + geom_segment(
        data=lines_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#2C2C2C", size=0.6, alpha=0.75
    )
    # Pattern overlays - stipple dots (sandstone)
    + geom_point(data=dots_df, mapping=aes(x="x", y="y"), color="#2C2C2C", size=1.0, alpha=0.65)
    # Pattern overlays - open circles (conglomerate)
    + geom_point(
        data=circles_df,
        mapping=aes(x="x", y="y"),
        color="#2C2C2C",
        size=3.5,
        alpha=0.55,
        shape="o",
        fill="none",
        stroke=0.9,
    )
    # Layer boundary lines
    + geom_segment(data=boundary_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#2C2C2C", size=0.8)
    # Unconformity wavy line (red - focal point for data storytelling)
    + geom_segment(
        data=wavy_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#B22222", size=1.8, alpha=0.9
    )
    # Unconformity annotation
    + annotate(
        "text",
        x=col_right + 0.4,
        y=unconformity_depth,
        label="~ Unconformity ~",
        ha="left",
        size=14,
        color="#B22222",
        fontstyle="italic",
        fontweight="bold",
    )
    # Age bracket lines using geom_linerange (idiomatic plotnine for vertical ranges)
    + geom_linerange(data=age_groups, mapping=aes(x="bracket_x", ymin="ymin", ymax="ymax"), color="#444444", size=0.8)
    # Formation labels using geom_label (plotnine-native styled text with background)
    + geom_label(
        data=form_groups,
        mapping=aes(x="x", y="mid", label="formation"),
        ha="left",
        size=16,
        fontstyle="italic",
        color="#1A1A1A",
        fill="#FFFFFF",
        alpha=0.7,
        label_padding=0.3,
        label_size=0,
    )
    # Age labels (left side)
    + geom_text(
        data=age_groups,
        mapping=aes(x="x", y="mid", label="age"),
        ha="right",
        size=15,
        fontweight="bold",
        color="#333333",
    )
    # Scales - grammar-driven fill mapping with manual color values
    + scale_fill_manual(values=lith_colors, name="Lithology")
    + scale_x_continuous(limits=(-4.5, 9.0), breaks=[])
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
        axis_text_y=element_text(size=18),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        legend_title=element_text(size=18, face="bold"),
        legend_text=element_text(size=16),
        legend_position="bottom",
        legend_direction="horizontal",
        legend_key_size=22,
        legend_background=element_rect(fill="#FAFAFA", color="#E0E0E0", size=0.3),
        legend_margin=10,
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3, alpha=0.4),
        panel_grid_minor_y=element_blank(),
        panel_background=element_rect(fill="#FAFAFA", color="none"),
        plot_background=element_rect(fill="white", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, width=12, height=16)
