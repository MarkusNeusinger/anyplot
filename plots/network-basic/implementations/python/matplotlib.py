""" pyplots.ai
network-basic: Basic Network Graph
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


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

# Calculate spring layout (force-directed algorithm)
n = len(nodes)
positions = np.random.rand(n, 2) * 2 - 1
k = 0.4  # Optimal distance parameter

for iteration in range(150):
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
    cooling = 1 - iteration / 150
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.1 * cooling)

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

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Colors for groups (Python Blue, Python Yellow, and colorblind-safe additions)
group_colors = ["#306998", "#FFD43B", "#4CAF50", "#FF7043"]

# Draw edges first
edge_lines = [[(pos[src][0], pos[src][1]), (pos[tgt][0], pos[tgt][1])] for src, tgt in edges]
lc = LineCollection(edge_lines, colors="#888888", linewidths=2.5, alpha=0.5, zorder=1)
ax.add_collection(lc)

# Draw nodes
for node in nodes:
    x, y = pos[node["id"]]
    size = 800 + degrees[node["id"]] * 200
    color = group_colors[node["group"]]
    ax.scatter(x, y, s=size, c=color, edgecolors="#333333", linewidths=2, alpha=0.9, zorder=2)

# Draw labels
for node in nodes:
    x, y = pos[node["id"]]
    ax.text(x, y, node["label"], fontsize=11, fontweight="bold", ha="center", va="center", color="#222222", zorder=3)

# Styling
ax.set_title("Social Network · network-basic · matplotlib · pyplots.ai", fontsize=24)
ax.set_xlim(-0.05, 1.05)
ax.set_ylim(-0.05, 1.05)
ax.axis("off")

# Add legend for groups
legend_labels = ["Group A", "Group B", "Group C", "Group D"]
legend_handles = [
    ax.scatter([], [], c=color, s=400, edgecolors="#333333", linewidths=2, label=label)
    for color, label in zip(group_colors, legend_labels, strict=True)
]
ax.legend(handles=legend_handles, loc="upper left", fontsize=16, framealpha=0.9, title="Communities", title_fontsize=18)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
