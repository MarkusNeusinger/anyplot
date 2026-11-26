"""anyplot.ai
network-force-directed: Force-Directed Graph
Library: letsplot 4.11.0 | Python 3.13.14
Quality: 86/100 | Updated: 2026-07-01
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
    gggrid,
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

# Imprint palette: all eight positions, one per community in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SOURCE = "Source"  # role: edges
TARGET = "Target"  # role: extra
WEIGHT = "Weight"  # role: weight
SOURCE_TEAM = "Source team"  # role: extra
TARGET_TEAM = "Target team"  # role: extra

# Data: replace this block with your own edge list, for example df = pd.read_csv("friendships.csv")
# 50-node social network with 3 communities; one row per friendship
np.random.seed(42)
community_sizes = [18, 17, 15]
community_names = ["Engineering", "Marketing", "Sales"]
team_of = [name for name, size in zip(community_names, community_sizes, strict=True) for _ in range(size)]
bounds = np.cumsum([0, *community_sizes])
rows = []
for start, end in zip(bounds[:-1], bounds[1:], strict=True):
    for i in range(start, end):
        for j in range(i + 1, end):
            if np.random.random() < 0.3:
                rows.append((i, j, np.random.uniform(0.5, 1.0)))
for src, tgt in [(0, 18), (5, 20), (10, 25), (18, 35), (22, 40), (30, 45), (8, 38), (15, 48)]:
    rows.append((src, tgt, np.random.uniform(0.2, 0.5)))
df = pd.DataFrame(rows, columns=[SOURCE, TARGET, WEIGHT])
df[SOURCE_TEAM] = [team_of[i] for i in df[SOURCE]]
df[TARGET_TEAM] = [team_of[i] for i in df[TARGET]]

# Plot
# Nodes come from the edge list, in id order
ids = np.unique(df[[SOURCE, TARGET]].to_numpy())
n = len(ids)
index = {node: i for i, node in enumerate(ids)}
src = df[SOURCE].map(index).to_numpy()
tgt = df[TARGET].map(index).to_numpy()
team_by_node = {
    **dict(zip(df[SOURCE], df[SOURCE_TEAM], strict=True)),
    **dict(zip(df[TARGET], df[TARGET_TEAM], strict=True)),
}

# Force-directed layout (Fruchterman-Reingold)
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
    for a, b in zip(src, tgt, strict=True):
        diff = positions[a] - positions[b]
        dist = max(np.linalg.norm(diff), 0.01)
        attractive = (dist * dist / k) * (diff / dist)
        displacement[a] -= attractive
        displacement[b] += attractive
    temperature = 1 - iteration / iterations
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.15 * temperature)

# Normalize positions to [0.05, 0.95]
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.9 + 0.05

# Plot frames: derived columns are named once here
X, Y, X_END, Y_END = "x", "y", "x_end", "y_end"
EDGE_SIZE, EDGE_ALPHA, NODE_SIZE, CONNECTIONS = "edge_size", "edge_alpha", "node_size", "Connections"
TEAM = "Team"

edges = pd.DataFrame(
    {
        X: positions[src, 0],
        Y: positions[src, 1],
        X_END: positions[tgt, 0],
        Y_END: positions[tgt, 1],
        EDGE_SIZE: 0.3 + df[WEIGHT].to_numpy() * 0.9,
        EDGE_ALPHA: 0.15 + df[WEIGHT].to_numpy() * 0.35,
    }
)
degrees = np.bincount(np.concatenate([src, tgt]), minlength=n)
nodes = pd.DataFrame(
    {
        X: positions[:, 0],
        Y: positions[:, 1],
        TEAM: [team_by_node[node] for node in ids],
        CONNECTIONS: degrees,
        NODE_SIZE: 4 + degrees * 0.9,
    }
)

# Title: len("network-force-directed · python · letsplot · anyplot.ai") = 55 < 67, no scaling
TITLE = "network-force-directed · python · letsplot · anyplot.ai"
title_size = 16

pad = 0.05
plot = (
    ggplot()
    + geom_segment(
        aes(x=X, y=Y, xend=X_END, yend=Y_END, size=EDGE_SIZE, alpha=EDGE_ALPHA),
        data=edges,
        color=EDGE_COLOR,
        tooltips="none",
    )
    + geom_point(
        aes(x=X, y=Y, color=TEAM, size=NODE_SIZE),
        data=nodes,
        stroke=1.0,
        alpha=0.92,
        tooltips=layer_tooltips().line(f"{TEAM}: @{TEAM}").line(f"{CONNECTIONS}: @{CONNECTIONS}"),
    )
    + scale_color_manual(values=IMPRINT_PALETTE, name=TEAM)
    + scale_size_identity(guide="none")
    + scale_alpha_identity(guide="none")
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(nodes[X].min() - pad, nodes[X].max() + pad))
    + scale_y_continuous(limits=(nodes[Y].min() - pad, nodes[Y].max() + pad))
    + labs(title=TITLE)
    + ggsize(600, 600)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=title_size, face="bold", color=INK),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_position=(0.02, 0.78),
        legend_justification=(0, 1),
    )
)

# The fixed aspect leaves canvas strips transparent: a one-panel grid paints the whole page
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save: ggsize(600, 600) x scale=4 -> 2400 x 2400 px
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
