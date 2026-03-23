""" pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    coord_fixed,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_rect,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_alpha_identity,
    scale_color_identity,
    scale_fill_identity,
    scale_shape_identity,
    scale_size_identity,
    theme,
    theme_void,
    xlim,
    ylim,
)


LetsPlot.setup_html()

# Data
np.random.seed(42)

n_events = 100
event_types = np.random.choice(["Pass", "Shot", "Tackle", "Interception"], size=n_events, p=[0.45, 0.15, 0.22, 0.18])

success_rates = {"Pass": 0.78, "Shot": 0.30, "Tackle": 0.60, "Interception": 0.70}
outcomes = [
    np.random.choice(["Successful", "Unsuccessful"], p=[success_rates[et], 1 - success_rates[et]]) for et in event_types
]

x_pos, y_pos, x_end, y_end = [], [], [], []
for et in event_types:
    if et == "Pass":
        x = np.random.uniform(10, 95)
        y = np.random.uniform(5, 63)
        dx = np.random.uniform(5, 25) * np.random.choice([-1, 1], p=[0.2, 0.8])
        dy = np.random.uniform(-15, 15)
        xe, ye = np.clip(x + dx, 0, 105), np.clip(y + dy, 0, 68)
    elif et == "Shot":
        x = np.random.uniform(55, 100)
        y = np.random.uniform(10, 58)
        xe, ye = 105.0, np.random.uniform(28, 40)
    else:
        x = np.random.uniform(15, 85)
        y = np.random.uniform(5, 63)
        xe, ye = x, y
    x_pos.append(x)
    y_pos.append(y)
    x_end.append(xe)
    y_end.append(ye)

# Colorblind-safe palette (distinct hues: blue, red, orange, purple)
pitch_green = "#2E7D32"
pass_color = "#FFD700"
shot_color = "#E63946"
tackle_color = "#F77F00"
intercept_color = "#7B2D8E"
color_map = {"Pass": pass_color, "Shot": shot_color, "Tackle": tackle_color, "Interception": intercept_color}
shape_map = {"Pass": 21, "Shot": 23, "Tackle": 24, "Interception": 22}

df = pd.DataFrame(
    {"x": x_pos, "y": y_pos, "x_end": x_end, "y_end": y_end, "event_type": event_types, "outcome": outcomes}
)
df["color"] = df["event_type"].map(color_map)
df["shape"] = df["event_type"].map(shape_map)
df["alpha"] = np.where(df["outcome"] == "Successful", 0.92, 0.85)
df["fill"] = np.where(df["outcome"] == "Successful", df["color"], "#FFFFFF")
df["marker_size"] = np.where(df["event_type"] == "Shot", 8.0, 5.0)

# Directional events (passes and shots)
df_arrows = df[df["event_type"].isin(["Pass", "Shot"])].copy()

# Pitch markings
theta = np.linspace(0, 2 * np.pi, 80)
df_center_circle = pd.DataFrame({"x": 52.5 + 9.15 * np.cos(theta), "y": 34 + 9.15 * np.sin(theta)})

theta_l = np.linspace(-np.pi / 2, np.pi / 2, 40)
arc_lx, arc_ly = 11 + 9.15 * np.cos(theta_l), 34 + 9.15 * np.sin(theta_l)
mask_l = arc_lx >= 16.5
df_left_arc = pd.DataFrame({"x": arc_lx[mask_l], "y": arc_ly[mask_l]})

theta_r = np.linspace(np.pi / 2, 3 * np.pi / 2, 40)
arc_rx, arc_ry = 94 + 9.15 * np.cos(theta_r), 34 + 9.15 * np.sin(theta_r)
mask_r = arc_rx <= 88.5
df_right_arc = pd.DataFrame({"x": arc_rx[mask_r], "y": arc_ry[mask_r]})

# Corner arcs (radius = 1m)
corner_positions = [
    (0, 0, 0, np.pi / 2),
    (0, 68, -np.pi / 2, 0),
    (105, 0, np.pi / 2, np.pi),
    (105, 68, np.pi, 3 * np.pi / 2),
]
corner_arc_dfs = []
for cx, cy, t_start, t_end in corner_positions:
    t = np.linspace(t_start, t_end, 20)
    corner_arc_dfs.append(pd.DataFrame({"x": cx + 1.0 * np.cos(t), "y": cy + 1.0 * np.sin(t)}))

# Pitch rectangles
df_rects = pd.DataFrame(
    {
        "xmin": [0, 0, 0, 88.5, 99.5],
        "ymin": [0, 13.84, 24.84, 13.84, 24.84],
        "xmax": [105, 16.5, 5.5, 105, 105],
        "ymax": [68, 54.16, 43.16, 54.16, 43.16],
    }
)

# Legend labels positioned below the pitch
legend_x = [12, 37, 62, 87]
legend_y_marker = [-7.5] * 4
legend_y_label = [-11.5] * 4
legend_labels = ["Pass", "Shot", "Tackle", "Interception"]
legend_colors = [pass_color, shot_color, tackle_color, intercept_color]
legend_shapes = [21, 23, 24, 22]

df_legend_markers = pd.DataFrame(
    {"x": legend_x, "y": legend_y_marker, "color": legend_colors, "shape": legend_shapes, "fill": legend_colors}
)
df_legend_labels = pd.DataFrame({"x": legend_x, "y": legend_y_label, "label": legend_labels})

# Outcome annotation
df_outcome_text = pd.DataFrame(
    {"x": [32, 72], "y": [-15.5, -15.5], "label": ["\u25cf Colored = Successful", "\u25cb White fill = Unsuccessful"]}
)

# Zone highlights for storytelling (attacking and defensive thirds)
df_attack_zone = pd.DataFrame({"xmin": [70], "ymin": [0], "xmax": [105], "ymax": [68]})
df_defend_zone = pd.DataFrame({"xmin": [0], "ymin": [0], "xmax": [35], "ymax": [68]})

# Plot
plot = (
    ggplot()
    # Pitch background
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=pd.DataFrame({"xmin": [-4], "ymin": [-4], "xmax": [109], "ymax": [72]}),
        fill=pitch_green,
        color=pitch_green,
    )
    # Zone highlights
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=df_attack_zone,
        fill="#FFFFFF",
        color="rgba(0,0,0,0)",
        alpha=0.08,
    )
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=df_defend_zone,
        fill="#000000",
        color="rgba(0,0,0,0)",
        alpha=0.06,
    )
    # Pitch markings
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax"),
        data=df_rects,
        fill="rgba(0,0,0,0)",
        color="#FFFFFF",
        size=1.0,
    )
    # Halfway line
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=pd.DataFrame({"x": [52.5], "y": [0], "xend": [52.5], "yend": [68]}),
        color="#FFFFFF",
        size=1.0,
    )
    # Goal posts
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=pd.DataFrame({"x": [0, 105], "y": [30.34, 30.34], "xend": [0, 105], "yend": [37.66, 37.66]}),
        color="#DDDDDD",
        size=2.5,
    )
    # Center circle and penalty arcs
    + geom_path(data=df_center_circle, mapping=aes(x="x", y="y"), color="#FFFFFF", size=1.0)
    + geom_path(data=df_left_arc, mapping=aes(x="x", y="y"), color="#FFFFFF", size=1.0)
    + geom_path(data=df_right_arc, mapping=aes(x="x", y="y"), color="#FFFFFF", size=1.0)
    # Corner arcs
    + geom_path(data=corner_arc_dfs[0], mapping=aes(x="x", y="y"), color="#FFFFFF", size=1.0)
    + geom_path(data=corner_arc_dfs[1], mapping=aes(x="x", y="y"), color="#FFFFFF", size=1.0)
    + geom_path(data=corner_arc_dfs[2], mapping=aes(x="x", y="y"), color="#FFFFFF", size=1.0)
    + geom_path(data=corner_arc_dfs[3], mapping=aes(x="x", y="y"), color="#FFFFFF", size=1.0)
    # Spots
    + geom_point(
        aes(x="x", y="y"), data=pd.DataFrame({"x": [52.5, 11, 94], "y": [34, 34, 34]}), color="#FFFFFF", size=2
    )
    # Directional arrows
    + geom_segment(
        data=df_arrows,
        mapping=aes(x="x", y="y", xend="x_end", yend="y_end", color="color", alpha="alpha"),
        size=0.8,
        arrow=arrow(length=7, type="open"),
    )
    # Event markers with size encoding (shots larger for focal emphasis)
    + geom_point(
        data=df,
        mapping=aes(x="x", y="y", color="color", fill="fill", shape="shape", alpha="alpha", size="marker_size"),
        stroke=1.5,
    )
    # Zone annotations
    + geom_text(
        data=pd.DataFrame({"x": [87.5], "y": [65.5], "label": ["Attacking Third"]}),
        mapping=aes(x="x", y="y", label="label"),
        size=10,
        color="#FFFFFF",
        alpha=0.55,
        fontface="italic",
    )
    + geom_text(
        data=pd.DataFrame({"x": [17.5], "y": [65.5], "label": ["Defensive Third"]}),
        mapping=aes(x="x", y="y", label="label"),
        size=10,
        color="#FFFFFF",
        alpha=0.45,
        fontface="italic",
    )
    # Legend markers
    + geom_point(
        data=df_legend_markers, mapping=aes(x="x", y="y", color="color", fill="fill", shape="shape"), size=6, stroke=1.2
    )
    # Legend labels
    + geom_text(
        data=df_legend_labels, mapping=aes(x="x", y="y", label="label"), size=15, color="#333333", fontface="bold"
    )
    # Outcome annotation
    + geom_text(data=df_outcome_text, mapping=aes(x="x", y="y", label="label"), size=12, color="#555555")
    + scale_color_identity()
    + scale_fill_identity()
    + scale_shape_identity()
    + scale_alpha_identity()
    + scale_size_identity()
    # Layout
    + coord_fixed(ratio=1)
    + xlim(-5, 112)
    + ylim(-19, 76)
    + labs(
        title="scatter-pitch-events \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="100 match events \u2014 passes, shots, tackles & interceptions with outcome encoding",
    )
    + theme_void()
    + theme(
        plot_title=element_text(size=26, hjust=0.5, color="#222222", face="bold"),
        plot_subtitle=element_text(size=16, hjust=0.5, color="#666666"),
        plot_background=element_rect(fill="#F5F5F0", color="#F5F5F0"),
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
