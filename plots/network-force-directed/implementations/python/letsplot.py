""" pyplots.ai
network-force-directed: Force-Directed Graph
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_blank,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Set seed for reproducibility
np.random.seed(42)

# Data: A social network with 50 nodes in 3 communities
# Demonstrates force-directed layout with clear community structure
nodes = []
edges = []

# Create 3 communities
community_sizes = [18, 17, 15]  # Total: 50 nodes
community_names = ["Engineering", "Marketing", "Sales"]
node_id = 0

for comm_idx, size in enumerate(community_sizes):
    for _ in range(size):
        nodes.append({"id": node_id, "community": comm_idx, "community_name": community_names[comm_idx]})
        node_id += 1

# Intra-community edges (dense connections within communities)
# Engineering: nodes 0-17
for i in range(18):
    for j in range(i + 1, 18):
        if np.random.random() < 0.3:
            edges.append((i, j))

# Marketing: nodes 18-34
for i in range(18, 35):
    for j in range(i + 1, 35):
        if np.random.random() < 0.3:
            edges.append((i, j))

# Sales: nodes 35-49
for i in range(35, 50):
    for j in range(i + 1, 50):
        if np.random.random() < 0.3:
            edges.append((i, j))

# Inter-community edges (sparse bridges between communities)
bridge_edges = [(0, 18), (5, 20), (10, 25), (18, 35), (22, 40), (30, 45), (8, 38), (15, 48)]
edges.extend(bridge_edges)

# Force-directed layout algorithm (Fruchterman-Reingold)
n = len(nodes)
positions = np.random.rand(n, 2) * 2 - 1  # Initial random positions

# Optimal distance parameter
k = 0.5
iterations = 200

for iteration in range(iterations):
    displacement = np.zeros((n, 2))

    # Repulsive forces between all node pairs (nodes push apart)
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            repulsive_force = (k * k / dist) * (diff / dist)
            displacement[i] += repulsive_force
            displacement[j] -= repulsive_force

    # Attractive forces along edges (connected nodes pull together)
    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        attractive_force = (dist * dist / k) * (diff / dist)
        displacement[src] -= attractive_force
        displacement[tgt] += attractive_force

    # Apply displacement with cooling (decreasing temperature)
    temperature = 1 - iteration / iterations
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            # Limit movement by temperature
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.15 * temperature)

# Normalize positions to [0.05, 0.95] range
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.9 + 0.05
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Calculate node degrees (number of connections)
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Create DataFrames for plotting
# Edges DataFrame
edges_df = pd.DataFrame(
    {
        "x": [pos[src][0] for src, tgt in edges],
        "y": [pos[src][1] for src, tgt in edges],
        "xend": [pos[tgt][0] for src, tgt in edges],
        "yend": [pos[tgt][1] for src, tgt in edges],
    }
)

# Nodes DataFrame
nodes_df = pd.DataFrame(
    {
        "x": [pos[node["id"]][0] for node in nodes],
        "y": [pos[node["id"]][1] for node in nodes],
        "community": [node["community_name"] for node in nodes],
        "degree": [degrees[node["id"]] for node in nodes],
        "size": [8 + degrees[node["id"]] * 2 for node in nodes],  # Scale size by connections
    }
)

# Community colors using Python Blue as primary
community_colors = ["#306998", "#FFD43B", "#FF6B6B"]

# Create plot
plot = (
    ggplot()
    # Draw edges first (behind nodes)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=edges_df, color="#AAAAAA", size=1.2, alpha=0.5)
    # Draw nodes colored by community and sized by degree
    + geom_point(aes(x="x", y="y", color="community", size="size"), data=nodes_df, stroke=2, alpha=0.85)
    + scale_color_manual(values=community_colors, name="Teams")
    + scale_size_identity()
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-0.05, 1.05))
    + scale_y_continuous(limits=(-0.05, 1.05))
    + labs(title="network-force-directed · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16),
        legend_position="left",
    )
)

# Save as PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML
ggsave(plot, "plot.html", path=".")
