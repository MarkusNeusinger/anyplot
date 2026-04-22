""" pyplots.ai
network-force-directed: Force-Directed Graph
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


# Set seed for reproducibility
np.random.seed(42)

# Data: A social network with 50 nodes in 3 communities
# Demonstrates force-directed layout with clear community structure
nodes = []
edges = []

# Create 3 communities representing company departments
community_sizes = [18, 17, 15]  # Total: 50 nodes
community_names = ["Engineering", "Marketing", "Sales"]
node_id = 0

for comm_idx, size in enumerate(community_sizes):
    for _ in range(size):
        nodes.append({"id": node_id, "community": comm_idx})
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

# Normalize positions to [0.08, 0.92] range for better margins
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.84 + 0.08
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Calculate node degrees (number of connections)
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Community colors (Python Blue, Python Yellow, and a colorblind-safe coral)
community_colors = ["#306998", "#FFD43B", "#E07B53"]

# Draw edges first (behind nodes)
edge_lines = [[(pos[src][0], pos[src][1]), (pos[tgt][0], pos[tgt][1])] for src, tgt in edges]
lc = LineCollection(edge_lines, colors="#888888", linewidths=1.5, alpha=0.35, zorder=1)
ax.add_collection(lc)

# Draw nodes sized by degree
for node in nodes:
    x, y = pos[node["id"]]
    degree = degrees[node["id"]]
    size = 450 + degree * 120  # Scale size by connections
    color = community_colors[node["community"]]
    ax.scatter(x, y, s=size, c=color, edgecolors="#333333", linewidths=1.5, alpha=0.85, zorder=2)

# Label only top hubs (highest degree nodes per community)
# Find top 2 nodes per community to avoid clutter
top_hubs = []
for comm_idx in range(3):
    comm_nodes = [n for n in nodes if n["community"] == comm_idx]
    comm_degrees = [(n["id"], degrees[n["id"]]) for n in comm_nodes]
    comm_degrees.sort(key=lambda x: x[1], reverse=True)
    top_hubs.extend([n_id for n_id, _ in comm_degrees[:2]])

for node in nodes:
    if node["id"] in top_hubs:
        x, y = pos[node["id"]]
        team_initial = community_names[node["community"]][0]
        ax.text(
            x,
            y + 0.045,
            f"Hub ({team_initial})",
            fontsize=14,
            fontweight="bold",
            ha="center",
            va="bottom",
            color="#333333",
            zorder=3,
        )

# Styling
ax.set_title("network-force-directed · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.axis("off")

# Legend for communities
legend_handles = [
    ax.scatter([], [], c=color, s=600, edgecolors="#333333", linewidths=1.5, label=name)
    for color, name in zip(community_colors, community_names, strict=True)
]
ax.legend(
    handles=legend_handles,
    loc="upper left",
    fontsize=16,
    framealpha=0.95,
    title="Teams",
    title_fontsize=18,
    edgecolor="#CCCCCC",
    fancybox=True,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
