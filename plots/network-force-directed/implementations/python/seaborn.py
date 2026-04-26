""" anyplot.ai
network-force-directed: Force-Directed Graph
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 86/100 | Updated: 2026-04-26
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
EDGE_COLOR = "#4A4A44" if THEME == "light" else "#B8B7B0"

sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

np.random.seed(42)

# Okabe-Ito categorical palette (first series always #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2"]

# Sample social network: organization with 3 departments
num_nodes = 37
community_sizes = [15, 12, 10]
community_names = ["Engineering", "Marketing", "Sales"]
communities = []
for comm_idx, size in enumerate(community_sizes):
    communities.extend([comm_idx] * size)

# Generate edges with community structure
edges = []
for i in range(num_nodes):
    for j in range(i + 1, num_nodes):
        if communities[i] == communities[j]:
            if np.random.random() < 0.35:
                weight = np.random.uniform(0.5, 1.0)
                edges.append((i, j, weight))
        else:
            if np.random.random() < 0.05:
                weight = np.random.uniform(0.3, 0.7)
                edges.append((i, j, weight))

# Calculate node degrees
degrees = [0] * num_nodes
for src, tgt, _ in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Identify bridge nodes (nodes with cross-community edges)
bridge_nodes = set()
for src, tgt, _ in edges:
    if communities[src] != communities[tgt]:
        bridge_nodes.add(src)
        bridge_nodes.add(tgt)

# Force-directed layout (Fruchterman-Reingold inline)
n = num_nodes
k = 0.5
iterations = 150

pos = np.random.rand(n, 2) * 2 - 1
t = 1.0
dt = t / (iterations + 1)

for _ in range(iterations):
    disp = np.zeros((n, 2))
    for i in range(n):
        for j in range(i + 1, n):
            delta = pos[i] - pos[j]
            dist = max(np.linalg.norm(delta), 0.01)
            force = (k * k) / dist
            force_vec = (delta / dist) * force
            disp[i] += force_vec
            disp[j] -= force_vec

    for src, tgt, _ in edges:
        delta = pos[src] - pos[tgt]
        dist = max(np.linalg.norm(delta), 0.01)
        force = (dist * dist) / k
        force_vec = (delta / dist) * force
        disp[src] -= force_vec
        disp[tgt] += force_vec

    for i in range(n):
        disp_norm = max(np.linalg.norm(disp[i]), 0.01)
        pos[i] += (disp[i] / disp_norm) * min(disp_norm, t)

    t -= dt

# Normalize positions
pos -= pos.mean(axis=0)
max_coord = np.abs(pos).max()
if max_coord > 0:
    pos /= max_coord

x_coords = pos[:, 0]
y_coords = pos[:, 1]

# Node sizes based on degree
node_sizes = [150 + degree * 60 for degree in degrees]

fig, ax = plt.subplots(figsize=(16, 9))

# Draw edges
for src, tgt, weight in edges:
    x0, y0 = pos[src]
    x1, y1 = pos[tgt]
    ax.plot([x0, x1], [y0, y1], color=EDGE_COLOR, linewidth=1 + weight * 2, alpha=0.25, zorder=1)

# Draw nodes via seaborn (Okabe-Ito palette)
sns.scatterplot(
    x=x_coords,
    y=y_coords,
    hue=communities,
    palette=OKABE_ITO,
    size=node_sizes,
    sizes=(150, 800),
    alpha=0.9,
    edgecolor=PAGE_BG,
    linewidth=2,
    ax=ax,
    legend=False,
    zorder=2,
)

# Emphasize bridge nodes (cross-community connectors) with a ring outline
bridge_x = [pos[i, 0] for i in bridge_nodes]
bridge_y = [pos[i, 1] for i in bridge_nodes]
bridge_sizes = [(node_sizes[i] + 200) for i in bridge_nodes]
ax.scatter(bridge_x, bridge_y, s=bridge_sizes, facecolors="none", edgecolors=INK, linewidth=1.8, alpha=0.65, zorder=3)

# Hub labels (75th-percentile degree threshold)
degree_threshold = np.percentile(degrees, 75)
for node in range(num_nodes):
    if degrees[node] >= degree_threshold:
        ax.annotate(
            f"Node {node}",
            (pos[node, 0], pos[node, 1]),
            fontsize=16,
            ha="center",
            va="bottom",
            xytext=(0, 12),
            textcoords="offset points",
            fontweight="bold",
            color=INK_SOFT,
        )

# Custom community legend
legend_elements = []
for idx, name in enumerate(community_names):
    count = community_sizes[idx]
    legend_elements.append(
        plt.scatter([], [], c=OKABE_ITO[idx], s=300, label=f"{name} ({count})", edgecolor=PAGE_BG, linewidth=2)
    )
legend_elements.append(
    plt.scatter([], [], s=300, facecolors="none", edgecolors=INK, linewidth=1.8, label="Bridge node")
)

ax.legend(
    handles=legend_elements,
    loc="upper left",
    fontsize=16,
    title="Department",
    title_fontsize=18,
    frameon=True,
    labelcolor=INK,
)

# Titles & labels
ax.set_title("network-force-directed · seaborn · anyplot.ai", fontsize=24, fontweight="bold", pad=20, color=INK)
ax.set_xlabel("Force-Directed X Position", fontsize=20, color=INK)
ax.set_ylabel("Force-Directed Y Position", fontsize=20, color=INK)
ax.tick_params(axis="both", labelsize=16)
ax.set_xticks([])
ax.set_yticks([])

# Spine treatment: keep L-shape only, themed color
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Network statistics annotation
total_edges = len(edges)
avg_degree = sum(degrees) / num_nodes
stats_text = f"Nodes: {num_nodes} | Edges: {total_edges} | Avg Degree: {avg_degree:.1f} | Bridges: {len(bridge_nodes)}"
ax.text(0.5, -0.08, stats_text, transform=ax.transAxes, fontsize=14, ha="center", va="top", color=INK_MUTED)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
