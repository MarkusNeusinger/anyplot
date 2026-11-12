"""anyplot.ai
hive-basic: Basic Hive Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-07
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
    scale_size_continuous,
    theme,
    theme_void,
    xlim,
    ylim,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per axis group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
FIRST_AXIS_ANGLE = 90  # degrees; the first group points up, the others follow clockwise
INNER_RADIUS = 0.1  # distance from the center of the lowest degree
OUTER_RADIUS = 0.95  # distance from the center of the highest degree

# Columns: set these to your tables' column names
NODE = "Module"  # role: nodes
GROUP = "Module type"  # role: axis_attribute
DEGREE = "Degree"  # role: extra
EDGE_ENDS = ["Source", "Target"]  # role: edges

# Data: replace this block with your own tables, for example df = pd.read_csv("edges.csv")
nodes = pd.DataFrame(
    {
        NODE: [
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
        GROUP: ["core"] * 7 + ["utility"] * 7 + ["interface"] * 7,
        DEGREE: [8, 7, 9, 6, 5, 4, 6, 5, 6, 4, 5, 4, 3, 4, 6, 5, 4, 5, 5, 3, 4],
    }
)
df = pd.DataFrame(
    {
        EDGE_ENDS[0]: [
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
        EDGE_ENDS[1]: [
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

# Plot: reads only df, nodes and the constants above
groups = nodes[GROUP].unique().tolist()
angles = {g: np.radians(FIRST_AXIS_ANGLE + 360 * i / len(groups)) for i, g in enumerate(groups)}
group_colors = {g: IMPRINT_PALETTE[i] for i, g in enumerate(groups)}

# Node positions: on the axis of the group, distance from the center set by degree
top_degree = nodes[DEGREE].max()
pos = nodes.copy()
pos["radius"] = INNER_RADIUS + (pos[DEGREE] / top_degree) * (OUTER_RADIUS - INNER_RADIUS)
pos["angle"] = pos[GROUP].map(angles)
pos["x"] = pos["radius"] * np.cos(pos["angle"])
pos["y"] = pos["radius"] * np.sin(pos["angle"])

# Perpendicular label positions beside each node
# (alternating sides along the axis keeps neighbouring labels apart)
label_offset = 0.05
rank = pos.groupby(GROUP)[DEGREE].rank(method="first")
side = np.where(rank % 2 == 0, 1, -1)
dist = label_offset + 0.09 * (((rank - 1) // 2) % 2)  # every other pair sits further out
pos["lx"] = pos["x"] + side * dist * np.cos(pos["angle"] + np.pi / 2)
pos["ly"] = pos["y"] + side * dist * np.sin(pos["angle"] + np.pi / 2)
# text grows away from the axis, so same-side neighbours never run into each other
pos["ha"] = np.where(pos["lx"] >= pos["x"], "left", "right")

# Axes and axis labels
axis_len = 1.0
axis_df = pd.DataFrame(
    {
        "x": 0.0,
        "y": 0.0,
        "xend": [axis_len * np.cos(angles[g]) for g in groups],
        "yend": [axis_len * np.sin(angles[g]) for g in groups],
        GROUP: groups,
    }
)
label_df = pd.DataFrame(
    {
        "x": [1.2 * np.cos(angles[g]) for g in groups],
        "y": [1.2 * np.sin(angles[g]) for g in groups],
        "label": [g.upper() for g in groups],
        GROUP: groups,
    }
)

# Edges: quadratic Bezier curves pulled toward the center, cut into short segments
lookup = pos.set_index(NODE)
n_steps = 20
t = np.linspace(0, 1, n_steps + 1)
curves = []
for src, tgt in zip(df[EDGE_ENDS[0]], df[EDGE_ENDS[1]], strict=True):
    p0 = lookup.loc[src, ["x", "y"]].to_numpy(dtype=float)
    p2 = lookup.loc[tgt, ["x", "y"]].to_numpy(dtype=float)
    same_axis = lookup.loc[src, GROUP] == lookup.loc[tgt, GROUP]
    p1 = (0.3 if same_axis else 0.15) * (p0 + p2) / 2
    pts = ((1 - t) ** 2)[:, None] * p0 + (2 * (1 - t) * t)[:, None] * p1 + (t**2)[:, None] * p2
    curves.append(
        pd.DataFrame(
            {"x": pts[:-1, 0], "y": pts[:-1, 1], "xend": pts[1:, 0], "yend": pts[1:, 1], GROUP: lookup.loc[src, GROUP]}
        )
    )
edge_df = pd.concat(curves, ignore_index=True)

plot = (
    ggplot()
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend", color=GROUP), data=edge_df, size=0.55, alpha=0.5)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend", color=GROUP), data=axis_df, size=1.3, alpha=0.8)
    + geom_point(aes(x="x", y="y", color=GROUP, size=DEGREE), data=pos, alpha=0.95)
    + geom_text(aes(x="lx", y="ly", label=NODE), data=pos[pos["ha"] == "left"], size=5.5, color=INK, ha="left")
    + geom_text(aes(x="lx", y="ly", label=NODE), data=pos[pos["ha"] == "right"], size=5.5, color=INK, ha="right")
    + geom_text(aes(x="x", y="y", label="label", color=GROUP), data=label_df, size=11, fontweight="bold")
    + scale_color_manual(values=group_colors, limits=groups)
    + scale_size_continuous(range=(2.5, 8))
    + coord_fixed(ratio=1)
    + xlim(-1.45, 1.45)
    + ylim(-1.45, 1.45)
    + labs(
        title="hive-basic · python · plotnine · anyplot.ai",
        caption="Distance from the center = module degree (number of connections)",
    )
    + theme_void()
    + theme(
        figure_size=(6, 6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=14, color=INK, weight="bold"),
        plot_caption=element_text(size=10, color=INK_SOFT),
        legend_position="none",
        plot_margin=0.02,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)
