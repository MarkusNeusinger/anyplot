"""anyplot.ai
network-force-directed: Force-Directed Graph
Library: letsplot | Python 3.13
Quality: 91/100 | Updated: 2026-04-26
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_alpha_identity,
    scale_color_manual,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
EDGE_COLOR = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Okabe-Ito categorical palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

# Data: 50-node social network with 3 communities
np.random.seed(42)

community_sizes = [18, 17, 15]
community_names = ["Engineering", "Marketing", "Sales"]
nodes = []
node_id = 0
for comm_idx, size in enumerate(community_sizes):
    for _ in range(size):
        nodes.append({"id": node_id, "community": comm_idx, "community_name": community_names[comm_idx]})
        node_id += 1

# Intra-community edges with weights (dense within communities)
edges = []
ranges = [(0, 18), (18, 35), (35, 50)]
for start, end in ranges:
    for i in range(start, end):
        for j in range(i + 1, end):
            if np.random.random() < 0.3:
                weight = np.random.uniform(0.5, 1.0)
                edges.append((i, j, weight))

# Inter-community bridge edges (lighter weights)
bridges = [(0, 18), (5, 20), (10, 25), (18, 35), (22, 40), (30, 45), (8, 38), (15, 48)]
for src, tgt in bridges:
    edges.append((src, tgt, np.random.uniform(0.2, 0.5)))

# Force-directed layout (Fruchterman-Reingold)
n = len(nodes)
positions = np.random.rand(n, 2) * 2 - 1
k = 0.5
iterations = 200

for iteration in range(iterations):
    displacement = np.zeros((n, 2))
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            repulsive = (k * k / dist) * (diff / dist)
            displacement[i] += repulsive
            displacement[j] -= repulsive
    for src, tgt, _ in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        attractive = (dist * dist / k) * (diff / dist)
        displacement[src] -= attractive
        displacement[tgt] += attractive
    temperature = 1 - iteration / iterations
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.15 * temperature)

# Normalize positions to [0.05, 0.95]
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.9 + 0.05
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Node degrees
degrees = {node["id"]: 0 for node in nodes}
for src, tgt, _ in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Edge DataFrame with weight-driven thickness
edges_df = pd.DataFrame(
    {
        "x": [pos[src][0] for src, tgt, _ in edges],
        "y": [pos[src][1] for src, tgt, _ in edges],
        "xend": [pos[tgt][0] for src, tgt, _ in edges],
        "yend": [pos[tgt][1] for src, tgt, _ in edges],
        "weight": [w for _, _, w in edges],
        "edge_size": [0.4 + w * 1.4 for _, _, w in edges],
        "edge_alpha": [0.15 + w * 0.35 for _, _, w in edges],
    }
)

# Node DataFrame
nodes_df = pd.DataFrame(
    {
        "x": [pos[node["id"]][0] for node in nodes],
        "y": [pos[node["id"]][1] for node in nodes],
        "Team": [node["community_name"] for node in nodes],
        "Connections": [degrees[node["id"]] for node in nodes],
        "size": [9 + degrees[node["id"]] * 1.8 for node in nodes],
    }
)

# Plot
plot = (
    ggplot()
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend", size="edge_size", alpha="edge_alpha"),
        data=edges_df,
        color=EDGE_COLOR,
        tooltips="none",
    )
    + geom_point(
        aes(x="x", y="y", color="Team", size="size"),
        data=nodes_df,
        stroke=1.5,
        alpha=0.92,
        tooltips=layer_tooltips().line("Team: @Team").line("Connections: @Connections"),
    )
    + scale_color_manual(values=OKABE_ITO, name="Team")
    + scale_size_identity(guide="none")
    + scale_alpha_identity(guide="none")
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-0.05, 1.05))
    + scale_y_continuous(limits=(-0.05, 1.05))
    + labs(title="network-force-directed · letsplot · anyplot.ai")
    + ggsize(1600, 900)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=24, face="bold", color=INK),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_position=(0.02, 0.78),
        legend_justification=(0, 1),
    )
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
