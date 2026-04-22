""" pyplots.ai
network-basic: Basic Network Graph
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
    geom_text,
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

# Data: A small social network with 20 people in 4 communities
nodes = [
    {"id": 0, "label": "Alice", "group": 0},
    {"id": 1, "label": "Bob", "group": 0},
    {"id": 2, "label": "Carol", "group": 0},
    {"id": 3, "label": "David", "group": 0},
    {"id": 4, "label": "Eve", "group": 0},
    {"id": 5, "label": "Frank", "group": 1},
    {"id": 6, "label": "Grace", "group": 1},
    {"id": 7, "label": "Henry", "group": 1},
    {"id": 8, "label": "Ivy", "group": 1},
    {"id": 9, "label": "Jack", "group": 1},
    {"id": 10, "label": "Kate", "group": 2},
    {"id": 11, "label": "Leo", "group": 2},
    {"id": 12, "label": "Mia", "group": 2},
    {"id": 13, "label": "Noah", "group": 2},
    {"id": 14, "label": "Olivia", "group": 2},
    {"id": 15, "label": "Paul", "group": 3},
    {"id": 16, "label": "Quinn", "group": 3},
    {"id": 17, "label": "Ryan", "group": 3},
    {"id": 18, "label": "Sara", "group": 3},
    {"id": 19, "label": "Tom", "group": 3},
]

# Edges: Friendship connections (within and between groups)
edges = [
    # Group 0 internal connections
    (0, 1),
    (0, 2),
    (1, 2),
    (1, 3),
    (2, 4),
    (3, 4),
    # Group 1 internal connections
    (5, 6),
    (5, 7),
    (6, 8),
    (7, 8),
    (7, 9),
    (8, 9),
    # Group 2 internal connections
    (10, 11),
    (10, 12),
    (11, 13),
    (12, 13),
    (12, 14),
    (13, 14),
    # Group 3 internal connections
    (15, 16),
    (15, 17),
    (16, 18),
    (17, 18),
    (17, 19),
    (18, 19),
    # Cross-group connections (bridges between communities)
    (0, 5),
    (4, 10),
    (9, 15),
    (14, 19),
    (2, 6),
    (8, 11),
    (13, 16),
]

# Initialize positions with group clustering for better layout
n = len(nodes)
group_centers = {
    0: np.array([-0.6, 0.6]),  # Top-left
    1: np.array([0.6, 0.6]),  # Top-right
    2: np.array([-0.6, -0.6]),  # Bottom-left
    3: np.array([0.6, -0.6]),  # Bottom-right
}
positions = np.zeros((n, 2))
for i, node in enumerate(nodes):
    center = group_centers[node["group"]]
    positions[i] = center + np.random.randn(2) * 0.2

k = 0.5  # Optimal distance parameter

# Force-directed layout iterations
for iteration in range(200):
    displacement = np.zeros((n, 2))

    # Repulsive forces between all node pairs
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            force = (k * k / dist) * (diff / dist)
            displacement[i] += force
            displacement[j] -= force

    # Attractive forces for edges
    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        force = (dist * dist / k) * (diff / dist)
        displacement[src] -= force
        displacement[tgt] += force

    # Apply displacement with cooling
    cooling = 1 - iteration / 200
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.08 * cooling)

# Normalize positions to [0.1, 0.9] range
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.8 + 0.1
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Calculate node degrees for sizing
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Group colors and names (Python Blue first, then Yellow, then additional accessible colors)
group_colors = ["#306998", "#FFD43B", "#2CA02C", "#E64A19"]
group_names = ["Research", "Marketing", "Engineering", "Design"]

# Create edges dataframe
edge_data = []
for src, tgt in edges:
    x0, y0 = pos[src]
    x1, y1 = pos[tgt]
    edge_data.append({"x": x0, "y": y0, "xend": x1, "yend": y1})

df_edges = pd.DataFrame(edge_data)

# Create nodes dataframe with label offset to reduce overlap
node_data = []
for node in nodes:
    x, y = pos[node["id"]]
    degree = degrees[node["id"]]
    node_data.append(
        {
            "x": x,
            "y": y,
            "label": node["label"],
            "group": group_names[node["group"]],
            "size": 8 + degree * 2,  # Scale size by degree
            "label_y": y + 0.04,  # Offset label above node
        }
    )

df_nodes = pd.DataFrame(node_data)

# Build the plot
plot = (
    ggplot()
    # Draw edges first (behind nodes)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_edges, color="#888888", size=1.2, alpha=0.4)
    # Draw nodes colored by group
    + geom_point(aes(x="x", y="y", color="group", size="size"), data=df_nodes, stroke=1.5, alpha=0.95)
    # Add node labels above nodes
    + geom_text(aes(x="x", y="label_y", label="label"), data=df_nodes, size=9, color="#333333", fontface="bold")
    + scale_color_manual(values=group_colors, name="Departments")
    + scale_size_identity()
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-0.05, 1.05))
    + scale_y_continuous(limits=(-0.05, 1.1))  # Extra space for labels
    + labs(title="Office Social Network · network-basic · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16, face="bold"),
        legend_position="right",
    )
)

# Save as PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML
ggsave(plot, "plot.html", path=".")
