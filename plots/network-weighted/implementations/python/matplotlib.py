""" pyplots.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Trade network between countries (billions USD)
np.random.seed(42)

# Define nodes (countries) with region groups
nodes = {
    "USA": {"group": "Americas"},
    "CAN": {"group": "Americas"},
    "MEX": {"group": "Americas"},
    "BRA": {"group": "Americas"},
    "DEU": {"group": "Europe"},
    "FRA": {"group": "Europe"},
    "GBR": {"group": "Europe"},
    "ITA": {"group": "Europe"},
    "CHN": {"group": "Asia"},
    "JPN": {"group": "Asia"},
    "KOR": {"group": "Asia"},
    "IND": {"group": "Asia"},
    "AUS": {"group": "Oceania"},
}

# Define edges with trade volume weights (billions USD)
edges = [
    ("USA", "CAN", 650),
    ("USA", "MEX", 580),
    ("USA", "CHN", 520),
    ("USA", "JPN", 180),
    ("USA", "DEU", 200),
    ("USA", "GBR", 130),
    ("USA", "KOR", 140),
    ("USA", "BRA", 80),
    ("CAN", "CHN", 75),
    ("CAN", "MEX", 40),
    ("MEX", "CHN", 90),
    ("DEU", "FRA", 170),
    ("DEU", "GBR", 120),
    ("DEU", "ITA", 130),
    ("DEU", "CHN", 200),
    ("FRA", "GBR", 90),
    ("FRA", "ITA", 80),
    ("FRA", "CHN", 65),
    ("GBR", "CHN", 95),
    ("CHN", "JPN", 280),
    ("CHN", "KOR", 250),
    ("CHN", "AUS", 180),
    ("CHN", "IND", 100),
    ("JPN", "KOR", 70),
    ("JPN", "AUS", 55),
    ("IND", "AUS", 30),
    ("BRA", "DEU", 20),
]

# Force-directed layout computation
node_list = list(nodes.keys())
n = len(node_list)
node_idx = {name: i for i, name in enumerate(node_list)}

# Initialize positions randomly
pos = np.random.rand(n, 2) * 2 - 1

k = 1.5 / np.sqrt(n)  # Optimal distance (increased for more spacing)
t = 0.5  # Temperature (step size)

for _ in range(300):
    disp = np.zeros((n, 2))

    # Repulsive forces between all pairs (stronger repulsion)
    for i in range(n):
        for j in range(i + 1, n):
            delta = pos[i] - pos[j]
            dist = max(np.linalg.norm(delta), 0.01)
            force = k * k / dist * 1.5  # Stronger repulsion
            direction = delta / dist
            disp[i] += direction * force
            disp[j] -= direction * force

    # Attractive forces along edges (weighted, but weaker)
    for src, tgt, weight in edges:
        i, j = node_idx[src], node_idx[tgt]
        delta = pos[i] - pos[j]
        dist = max(np.linalg.norm(delta), 0.01)
        force = dist * dist / k * (0.8 + weight / 400)  # Weaker attraction
        direction = delta / dist
        disp[i] -= direction * force
        disp[j] += direction * force

    # Apply displacement with temperature limiting
    for i in range(n):
        disp_norm = max(np.linalg.norm(disp[i]), 0.01)
        pos[i] += disp[i] / disp_norm * min(disp_norm, t)

    t *= 0.97  # Cool down more slowly

# Normalize positions to [-1, 1]
pos_min = pos.min(axis=0)
pos_max = pos.max(axis=0)
pos = 2 * (pos - pos_min) / (pos_max - pos_min + 0.001) - 1
pos *= 0.75  # More compact to avoid clipping

# Store positions
positions = {name: pos[node_idx[name]] for name in node_list}

# Compute weighted degree for node sizing
weighted_degree = dict.fromkeys(nodes, 0)
for src, tgt, weight in edges:
    weighted_degree[src] += weight
    weighted_degree[tgt] += weight

# Color mapping by region
group_colors = {
    "Americas": "#306998",  # Python Blue
    "Europe": "#FFD43B",  # Python Yellow
    "Asia": "#E74C3C",  # Red
    "Oceania": "#2ECC71",  # Green
}

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Edge width and alpha scaling
edge_weights = [w for _, _, w in edges]
max_weight = max(edge_weights)
min_weight = min(edge_weights)
weight_range = max_weight - min_weight

# Draw edges with varying thickness
for src, tgt, weight in edges:
    pos_src = positions[src]
    pos_tgt = positions[tgt]
    norm_w = (weight - min_weight) / weight_range if weight_range > 0 else 0.5
    line_width = 1.5 + norm_w * 10
    alpha = 0.3 + norm_w * 0.5
    ax.plot(
        [pos_src[0], pos_tgt[0]],
        [pos_src[1], pos_tgt[1]],
        color="#666666",
        linewidth=line_width,
        alpha=alpha,
        solid_capstyle="round",
        zorder=1,
    )

# Node sizes based on weighted degree (scaled for visibility)
max_degree = max(weighted_degree.values())
node_sizes = {name: 400 + (weighted_degree[name] / max_degree) * 2000 for name in nodes}

# Draw nodes
for name, data in nodes.items():
    color = group_colors[data["group"]]
    node_pos = positions[name]
    ax.scatter(node_pos[0], node_pos[1], s=node_sizes[name], c=color, edgecolors="white", linewidths=2.5, zorder=2)

# Draw node labels (above nodes to avoid overlap)
for name in nodes:
    node_pos = positions[name]
    # Calculate offset based on node size (place label above node)
    node_radius = np.sqrt(node_sizes[name]) / 100  # Approximate radius in data coords
    ax.annotate(
        name,
        (node_pos[0], node_pos[1] + node_radius + 0.06),
        fontsize=14,
        fontweight="bold",
        ha="center",
        va="bottom",
        color="#333333",
        zorder=3,
    )

# Region legend
legend_handles = []
for region, color in group_colors.items():
    handle = ax.scatter([], [], s=400, c=color, edgecolors="white", linewidths=2, label=region)
    legend_handles.append(handle)

ax.legend(handles=legend_handles, loc="upper left", fontsize=16, framealpha=0.9, title="Region", title_fontsize=18)

# Edge thickness legend
legend_text = f"Edge thickness: Trade volume\n(${min_weight}B - ${max_weight}B USD)"
ax.annotate(
    legend_text,
    xy=(0.02, 0.02),
    xycoords="axes fraction",
    fontsize=14,
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
    verticalalignment="bottom",
)

# Style
ax.set_title("network-weighted · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlim(-1.15, 1.15)
ax.set_ylim(-1.15, 1.15)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
