""" pyplots.ai
network-basic: Basic Network Graph
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn style
sns.set_theme(style="white", context="talk", font_scale=1.2)

# Seed for reproducibility
np.random.seed(42)

# Data: A small social network with 20 people in 4 communities
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

# Edges: Friendship connections (within and between groups)
edges = [
    # Team A internal connections
    (0, 1),
    (0, 2),
    (1, 2),
    (1, 3),
    (2, 4),
    (3, 4),
    # Team B internal connections
    (5, 6),
    (5, 7),
    (6, 8),
    (7, 8),
    (7, 9),
    (8, 9),
    # Team C internal connections
    (10, 11),
    (10, 12),
    (11, 13),
    (12, 13),
    (12, 14),
    (13, 14),
    # Team D internal connections
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

# Calculate node degrees
n = len(nodes)
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Spring layout (force-directed algorithm)
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

# Create DataFrame for seaborn
node_data = []
for i, node in enumerate(nodes):
    node_data.append(
        {
            "x": positions[i, 0],
            "y": positions[i, 1],
            "label": node["label"],
            "group": node["group"],
            "size": 500 + degrees[node["id"]] * 150,  # Size by connections
        }
    )
df_nodes = pd.DataFrame(node_data)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw edges first using matplotlib (edges are structural, not data)
for src, tgt in edges:
    x_vals = [positions[src, 0], positions[tgt, 0]]
    y_vals = [positions[src, 1], positions[tgt, 1]]
    ax.plot(x_vals, y_vals, color="#888888", linewidth=2, alpha=0.4, zorder=1)

# Draw nodes using seaborn scatterplot with hue for groups
palette = {"Team A": "#306998", "Team B": "#FFD43B", "Team C": "#4CAF50", "Team D": "#FF7043"}
sns.scatterplot(
    data=df_nodes,
    x="x",
    y="y",
    hue="group",
    size="size",
    sizes=(400, 1200),
    palette=palette,
    edgecolor="#333333",
    linewidth=2,
    alpha=0.9,
    legend="brief",
    ax=ax,
    zorder=2,
)

# Draw labels on nodes
for _, row in df_nodes.iterrows():
    ax.text(
        row["x"],
        row["y"],
        row["label"],
        fontsize=11,
        fontweight="bold",
        ha="center",
        va="center",
        color="#222222",
        zorder=3,
    )

# Style the plot
ax.set_title("Social Network · network-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold")
ax.set_xlim(-0.05, 1.05)
ax.set_ylim(-0.05, 1.05)
ax.axis("off")

# Customize legend (remove size legend, keep only group legend)
handles, labels = ax.get_legend_handles_labels()
# Filter out size legend entries
group_handles = [h for h, lbl in zip(handles, labels, strict=False) if lbl in palette]
group_labels = [lbl for lbl in labels if lbl in palette]
ax.legend(
    group_handles, group_labels, loc="upper left", fontsize=14, framealpha=0.9, title="Community", title_fontsize=16
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
