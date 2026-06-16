""" anyplot.ai
network-force-directed: Force-Directed Graph
Library: matplotlib 3.10.9 | Python 3.14.4
Quality: 85/100 | Updated: 2026-04-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette — first series is always #009E73
COMMUNITY_COLORS = ["#009E73", "#C475FD", "#4467A3"]
COMMUNITY_NAMES = ["Engineering", "Marketing", "Sales"]

# Data: a 50-person company social network with 3 departments
np.random.seed(42)
community_sizes = [18, 17, 15]

nodes = []
node_id = 0
for comm_idx, size in enumerate(community_sizes):
    for _ in range(size):
        nodes.append({"id": node_id, "community": comm_idx})
        node_id += 1

edges = []
# Intra-community edges (dense connections within departments)
ranges = [(0, 18), (18, 35), (35, 50)]
for start, stop in ranges:
    for i in range(start, stop):
        for j in range(i + 1, stop):
            if np.random.random() < 0.3:
                edges.append((i, j))

# Inter-community edges (sparse bridges between departments)
bridge_edges = [(0, 18), (5, 20), (10, 25), (18, 35), (22, 40), (30, 45), (8, 38), (15, 48)]
edges.extend(bridge_edges)

# Force-directed layout (Fruchterman-Reingold)
n = len(nodes)
positions = np.random.rand(n, 2) * 2 - 1
k = 0.5
iterations = 200

for iteration in range(iterations):
    displacement = np.zeros((n, 2))

    # Repulsive forces between all node pairs
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            repulsive_force = (k * k / dist) * (diff / dist)
            displacement[i] += repulsive_force
            displacement[j] -= repulsive_force

    # Attractive forces along edges
    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        attractive_force = (dist * dist / k) * (diff / dist)
        displacement[src] -= attractive_force
        displacement[tgt] += attractive_force

    # Apply displacement with cooling
    temperature = 1 - iteration / iterations
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.15 * temperature)

# Normalize positions to [0.08, 0.92] for comfortable margins
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.84 + 0.08
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Node degrees
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Edges (behind nodes), theme-adaptive low-contrast color
edge_lines = [[(pos[src][0], pos[src][1]), (pos[tgt][0], pos[tgt][1])] for src, tgt in edges]
lc = LineCollection(edge_lines, colors=INK_SOFT, linewidths=1.5, alpha=0.30, zorder=1)
ax.add_collection(lc)

# Nodes sized by degree
node_sizes = {}
for node in nodes:
    x, y = pos[node["id"]]
    degree = degrees[node["id"]]
    size = 450 + degree * 120
    node_sizes[node["id"]] = size
    color = COMMUNITY_COLORS[node["community"]]
    ax.scatter(x, y, s=size, c=color, edgecolors=PAGE_BG, linewidths=2.0, alpha=0.92, zorder=2)

# Label top 2 hubs per community, with size-aware offset to prevent overlap
top_hubs = []
for comm_idx in range(3):
    comm_degrees = [(node["id"], degrees[node["id"]]) for node in nodes if node["community"] == comm_idx]
    comm_degrees.sort(key=lambda x: x[1], reverse=True)
    top_hubs.extend([node_id for node_id, _ in comm_degrees[:2]])

for node in nodes:
    node_id = node["id"]
    if node_id in top_hubs:
        x, y = pos[node_id]
        # Offset scales with marker radius (s is area in pt²)
        offset = 0.012 + 0.0009 * np.sqrt(node_sizes[node_id])
        team_initial = COMMUNITY_NAMES[node["community"]][0]
        ax.text(
            x,
            y + offset,
            f"Hub ({team_initial})",
            fontsize=14,
            fontweight="bold",
            ha="center",
            va="bottom",
            color=INK,
            zorder=4,
            bbox={"facecolor": ELEVATED_BG, "edgecolor": "none", "boxstyle": "round,pad=0.25", "alpha": 0.85},
        )

# Title and frame
ax.set_title("network-force-directed · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.axis("off")

# Legend
legend_handles = [
    ax.scatter([], [], c=color, s=600, edgecolors=PAGE_BG, linewidths=2.0, label=name)
    for color, name in zip(COMMUNITY_COLORS, COMMUNITY_NAMES, strict=True)
]
leg = ax.legend(
    handles=legend_handles,
    loc="upper left",
    fontsize=16,
    title="Teams",
    title_fontsize=18,
    framealpha=0.95,
    fancybox=True,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_title().set_color(INK)
plt.setp(leg.get_texts(), color=INK_SOFT)

# Footer
fig.text(
    0.5,
    0.02,
    f"50 nodes · {len(edges)} edges · node size scales with degree",
    ha="center",
    va="bottom",
    fontsize=12,
    color=INK_MUTED,
)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
