""" anyplot.ai
network-basic: Basic Network Graph
Library: plotnine 0.15.3 | Python 3.14.4
Quality: 76/100 | Created: 2026-04-27
"""

import os
import sys

import numpy as np
import pandas as pd


try:
    from plotnine import (
        aes,
        coord_cartesian,
        element_blank,
        element_rect,
        element_text,
        geom_point,
        geom_segment,
        geom_text,
        ggplot,
        guides,
        labs,
        scale_color_manual,
        scale_size_continuous,
        theme,
    )
except ImportError:
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path = [p for p in sys.path if os.path.abspath(p) != _this_dir]
    from plotnine import (
        aes,
        coord_cartesian,
        element_blank,
        element_rect,
        element_text,
        geom_point,
        geom_segment,
        geom_text,
        ggplot,
        guides,
        labs,
        scale_color_manual,
        scale_size_continuous,
        theme,
    )

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data: social network with 20 people in 4 communities
np.random.seed(42)

nodes = [
    {"id": 0, "label": "Alice", "group": "Team A"},
    {"id": 1, "label": "Bob", "group": "Team A"},
    {"id": 2, "label": "Carol", "group": "Team A"},
    {"id": 3, "label": "David", "group": "Team A"},
    {"id": 4, "label": "Eve", "group": "Team A"},
    {"id": 5, "label": "Frank", "group": "Team B"},
    {"id": 6, "label": "Grace", "group": "Team B"},
    {"id": 7, "label": "Henry", "group": "Team B"},
    {"id": 8, "label": "Ivy", "group": "Team B"},
    {"id": 9, "label": "Jack", "group": "Team B"},
    {"id": 10, "label": "Kate", "group": "Team C"},
    {"id": 11, "label": "Leo", "group": "Team C"},
    {"id": 12, "label": "Mia", "group": "Team C"},
    {"id": 13, "label": "Noah", "group": "Team C"},
    {"id": 14, "label": "Olivia", "group": "Team C"},
    {"id": 15, "label": "Paul", "group": "Team D"},
    {"id": 16, "label": "Quinn", "group": "Team D"},
    {"id": 17, "label": "Ryan", "group": "Team D"},
    {"id": 18, "label": "Sara", "group": "Team D"},
    {"id": 19, "label": "Tom", "group": "Team D"},
]

edges = [
    (0, 1),
    (0, 2),
    (1, 2),
    (1, 3),
    (2, 4),
    (3, 4),
    (5, 6),
    (5, 7),
    (6, 8),
    (7, 8),
    (7, 9),
    (8, 9),
    (10, 11),
    (10, 12),
    (11, 13),
    (12, 13),
    (12, 14),
    (13, 14),
    (15, 16),
    (15, 17),
    (16, 18),
    (17, 18),
    (17, 19),
    (18, 19),
    (0, 5),
    (4, 10),
    (9, 15),
    (14, 19),
    (2, 6),
    (8, 11),
    (13, 16),
]

# Node degrees
n = len(nodes)
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Spring layout (force-directed algorithm)
positions = np.random.rand(n, 2) * 2 - 1
k = 0.4

for iteration in range(150):
    displacement = np.zeros((n, 2))

    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            force = (k * k / dist) * (diff / dist)
            displacement[i] += force
            displacement[j] -= force

    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        force = (dist * dist / k) * (diff / dist)
        displacement[src] -= force
        displacement[tgt] += force

    cooling = 1 - iteration / 150
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.1 * cooling)

pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.8 + 0.1

# Build DataFrames
node_df = pd.DataFrame(
    {
        "x": [positions[i, 0] for i in range(n)],
        "y": [positions[i, 1] for i in range(n)],
        "label": [node["label"] for node in nodes],
        "group": [node["group"] for node in nodes],
        "degree": [float(degrees[node["id"]]) for node in nodes],
    }
)

edge_df = pd.DataFrame(
    [
        {"x": positions[src, 0], "y": positions[src, 1], "xend": positions[tgt, 0], "yend": positions[tgt, 1]}
        for src, tgt in edges
    ]
)

group_colors = {"Team A": OKABE_ITO[0], "Team B": OKABE_ITO[1], "Team C": OKABE_ITO[2], "Team D": OKABE_ITO[3]}

# Plot
plot = (
    ggplot()
    + geom_segment(
        data=edge_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color=INK_SOFT, size=0.7, alpha=0.45
    )
    + geom_point(data=node_df, mapping=aes(x="x", y="y", color="group", size="degree"), alpha=0.92)
    + geom_text(data=node_df, mapping=aes(x="x", y="y", label="label"), color=INK, size=7, nudge_y=0.045, va="bottom")
    + scale_color_manual(values=group_colors, name="Community")
    + scale_size_continuous(range=(6, 18))
    + guides(size=None)
    + coord_cartesian(xlim=(-0.05, 1.05), ylim=(-0.05, 1.05))
    + labs(title="Social Network · network-basic · plotnine · anyplot.ai")
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        panel_border=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        plot_title=element_text(color=INK, size=24, ha="center"),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(color=INK_SOFT, size=16),
        legend_title=element_text(color=INK, size=18),
        legend_key=element_rect(fill=ELEVATED_BG),
    )
)

plot.save(f"plot-{THEME}.png", dpi=300, width=16, height=9)
