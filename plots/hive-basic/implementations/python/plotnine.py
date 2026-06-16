""" anyplot.ai
hive-basic: Basic Hive Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-07
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_void,
    xlim,
    ylim,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"
COLOR_2 = "#C475FD"
COLOR_3 = "#4467A3"

np.random.seed(42)

nodes = pd.DataFrame(
    {
        "id": [
            "auth",
            "db",
            "core",
            "session",
            "kernel",
            "runtime",
            "engine",
            "cache",
            "logger",
            "config",
            "validator",
            "crypto",
            "parser",
            "queue",
            "api",
            "web",
            "cli",
            "router",
            "http",
            "grpc",
            "websocket",
        ],
        "category": [
            "core",
            "core",
            "core",
            "core",
            "core",
            "core",
            "core",
            "utility",
            "utility",
            "utility",
            "utility",
            "utility",
            "utility",
            "utility",
            "interface",
            "interface",
            "interface",
            "interface",
            "interface",
            "interface",
            "interface",
        ],
        "degree": [8, 7, 9, 6, 5, 4, 6, 5, 6, 4, 5, 4, 3, 4, 6, 5, 4, 5, 5, 3, 4],
    }
)

edges = pd.DataFrame(
    {
        "source": [
            "api",
            "api",
            "api",
            "web",
            "web",
            "web",
            "cli",
            "cli",
            "auth",
            "auth",
            "auth",
            "db",
            "db",
            "cache",
            "logger",
            "config",
            "validator",
            "core",
            "core",
            "core",
            "router",
            "router",
            "session",
            "session",
            "http",
            "crypto",
            "grpc",
            "websocket",
            "kernel",
            "runtime",
        ],
        "target": [
            "auth",
            "db",
            "logger",
            "auth",
            "session",
            "router",
            "config",
            "logger",
            "db",
            "crypto",
            "session",
            "cache",
            "logger",
            "logger",
            "config",
            "validator",
            "logger",
            "db",
            "cache",
            "logger",
            "http",
            "auth",
            "cache",
            "crypto",
            "parser",
            "parser",
            "auth",
            "session",
            "runtime",
            "engine",
        ],
    }
)

axis_angles = {"core": 90, "utility": 210, "interface": 330}
axis_colors = {"core": BRAND, "utility": COLOR_2, "interface": COLOR_3}

max_degree = nodes["degree"].max()

nodes_by_category = {}
for cat in ["core", "utility", "interface"]:
    cat_nodes = nodes[nodes["category"] == cat].sort_values("degree", ascending=False).reset_index(drop=True)
    nodes_by_category[cat] = cat_nodes

positions = []
for cat, cat_nodes in nodes_by_category.items():
    angle_deg = axis_angles[cat]
    angle_rad = np.radians(angle_deg)

    for _idx, row in cat_nodes.iterrows():
        base_radius = 0.25 + (row["degree"] / max_degree) * 0.70

        x = base_radius * np.cos(angle_rad)
        y = base_radius * np.sin(angle_rad)

        node_size = 6 + (row["degree"] / max_degree) * 16

        positions.append(
            {
                "id": row["id"],
                "x": x,
                "y": y,
                "category": row["category"],
                "degree": row["degree"],
                "node_size": node_size,
            }
        )

node_positions = pd.DataFrame(positions)

axis_lines = []
for cat, angle in axis_angles.items():
    angle_rad = np.radians(angle)
    axis_lines.append(
        {"x": 0, "y": 0, "xend": 1.0 * np.cos(angle_rad), "yend": 1.0 * np.sin(angle_rad), "category": cat}
    )
axis_df = pd.DataFrame(axis_lines)

edge_data = []
for _, row in edges.iterrows():
    src_match = node_positions[node_positions["id"] == row["source"]]
    tgt_match = node_positions[node_positions["id"] == row["target"]]

    if len(src_match) == 0 or len(tgt_match) == 0:
        continue

    src_pos = src_match.iloc[0]
    tgt_pos = tgt_match.iloc[0]

    src_cat = src_pos["category"]
    tgt_cat = tgt_pos["category"]

    if src_cat == tgt_cat:
        mid_factor = 0.3
    else:
        mid_factor = 0.15

    ctrl_x = mid_factor * (src_pos["x"] + tgt_pos["x"]) / 2
    ctrl_y = mid_factor * (src_pos["y"] + tgt_pos["y"]) / 2

    n_points = 20
    for i in range(n_points):
        t0 = i / n_points
        t1 = (i + 1) / n_points

        x0 = (1 - t0) ** 2 * src_pos["x"] + 2 * (1 - t0) * t0 * ctrl_x + t0**2 * tgt_pos["x"]
        y0 = (1 - t0) ** 2 * src_pos["y"] + 2 * (1 - t0) * t0 * ctrl_y + t0**2 * tgt_pos["y"]
        x1 = (1 - t1) ** 2 * src_pos["x"] + 2 * (1 - t1) * t1 * ctrl_x + t1**2 * tgt_pos["x"]
        y1 = (1 - t1) ** 2 * src_pos["y"] + 2 * (1 - t1) * t1 * ctrl_y + t1**2 * tgt_pos["y"]

        edge_data.append(
            {
                "x": x0,
                "y": y0,
                "xend": x1,
                "yend": y1,
                "src_cat": src_cat,
                "tgt_cat": tgt_cat,
                "edge_color": axis_colors[src_cat],
            }
        )

edge_df = pd.DataFrame(edge_data)

axis_labels = []
for cat, angle in axis_angles.items():
    angle_rad = np.radians(angle)
    axis_labels.append(
        {"x": 1.18 * np.cos(angle_rad), "y": 1.18 * np.sin(angle_rad), "label": cat.upper(), "category": cat}
    )
label_df = pd.DataFrame(axis_labels)

node_labels = []
for _, row in node_positions.iterrows():
    angle_deg = axis_angles[row["category"]]
    angle_rad = np.radians(angle_deg)

    offset = 0.18
    perp_angle = angle_rad + np.pi / 2
    label_x = row["x"] + offset * np.cos(perp_angle)
    label_y = row["y"] + offset * np.sin(perp_angle)

    node_labels.append({"x": label_x, "y": label_y, "label": row["id"], "category": row["category"]})
node_labels_df = pd.DataFrame(node_labels)

plot = (
    ggplot()
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend", color="src_cat"), data=edge_df, size=1.5, alpha=0.5)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend", color="category"), data=axis_df, size=3.5, alpha=0.8)
    + geom_point(aes(x="x", y="y", color="category", size="node_size"), data=node_positions, alpha=0.95)
    + geom_text(aes(x="x", y="y", label="label"), data=node_labels_df, size=10, color=INK)
    + geom_text(aes(x="x", y="y", label="label", color="category"), data=label_df, size=18)
    + scale_color_manual(values=axis_colors)
    + coord_fixed(ratio=1)
    + xlim(-1.6, 1.6)
    + ylim(-1.6, 1.6)
    + labs(title="hive-basic · plotnine · anyplot.ai")
    + theme_void()
    + theme(
        figure_size=(16, 16),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=28, color=INK, weight="bold"),
        legend_position="none",
        plot_margin=0.01,
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
