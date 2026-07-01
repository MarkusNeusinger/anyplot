"""anyplot.ai
network-force-directed: Force-Directed Graph
Library: matplotlib | Python
"""

import os
import pathlib

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


OUTPUT_DIR = pathlib.Path(__file__).parent


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — first series is always #009E73
COMMUNITY_COLORS = ["#009E73", "#C475FD", "#4467A3"]
COMMUNITY_NAMES = ["Engineering", "Marketing", "Sales"]

# Data: 50-person company social network with 3 departments
np.random.seed(42)
community_sizes = [18, 17, 15]

nodes = []
nid_counter = 0
for comm_idx, size in enumerate(community_sizes):
    for _ in range(size):
        nodes.append({"id": nid_counter, "community": comm_idx})
        nid_counter += 1

intra_edges = []
ranges = [(0, 18), (18, 35), (35, 50)]
for start, stop in ranges:
    for i in range(start, stop):
        for j in range(i + 1, stop):
            if np.random.random() < 0.3:
                intra_edges.append((i, j))

# Sparse cross-department bridge edges
bridge_edges = [(0, 18), (5, 20), (10, 25), (18, 35), (22, 40), (30, 45), (8, 38), (15, 48)]
all_edges = intra_edges + bridge_edges

# Force-directed layout (Fruchterman-Reingold)
n = len(nodes)
positions = np.random.rand(n, 2) * 2 - 1
k = 0.5

for iteration in range(200):
    displacement = np.zeros((n, 2))

    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            repulsive_force = (k * k / dist) * (diff / dist)
            displacement[i] += repulsive_force
            displacement[j] -= repulsive_force

    for src, tgt in all_edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        attractive_force = (dist * dist / k) * (diff / dist)
        displacement[src] -= attractive_force
        displacement[tgt] += attractive_force

    temperature = 1 - iteration / 200
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.15 * temperature)

pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.84 + 0.08
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

degrees = {node["id"]: 0 for node in nodes}
for src, tgt in all_edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Canvas: 3200×1800 px (landscape 16:9)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Intra-community edges (solid, subtle — dense within-team connections)
intra_lines = [(pos[src], pos[tgt]) for src, tgt in intra_edges]
lc_intra = LineCollection(intra_lines, colors=INK_SOFT, linewidths=0.7, alpha=0.22, zorder=1)
ax.add_collection(lc_intra)

# Bridge edges (dashed, more visible — sparse cross-team connections reveal structure)
bridge_lines = [(pos[src], pos[tgt]) for src, tgt in bridge_edges]
lc_bridge = LineCollection(bridge_lines, colors=INK_MUTED, linewidths=1.2, alpha=0.65, linestyle="dashed", zorder=1)
ax.add_collection(lc_bridge)

# Nodes sized by degree
node_sizes = {}
for node in nodes:
    x, y = pos[node["id"]]
    degree = degrees[node["id"]]
    size = 80 + degree * 12
    node_sizes[node["id"]] = size
    color = COMMUNITY_COLORS[node["community"]]
    ax.scatter(x, y, s=size, c=color, edgecolors=PAGE_BG, linewidths=1.2, alpha=0.92, zorder=2)

# Label top 2 hubs per community
top_hubs = []
for comm_idx in range(3):
    comm_degrees = [(node["id"], degrees[node["id"]]) for node in nodes if node["community"] == comm_idx]
    comm_degrees.sort(key=lambda x: x[1], reverse=True)
    top_hubs.extend([nid for nid, _ in comm_degrees[:2]])

for node in nodes:
    nid = node["id"]
    if nid in top_hubs:
        x, y = pos[nid]
        offset = 0.008 + 0.0007 * np.sqrt(node_sizes[nid])
        team_initial = COMMUNITY_NAMES[node["community"]][0]
        ax.text(
            x,
            y + offset,
            f"Hub ({team_initial})",
            fontsize=8,
            fontweight="bold",
            ha="center",
            va="bottom",
            color=INK,
            zorder=4,
            bbox={"facecolor": ELEVATED_BG, "edgecolor": "none", "boxstyle": "round,pad=0.2", "alpha": 0.85},
        )

title = "network-force-directed · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.axis("off")

legend_handles = [
    ax.scatter([], [], c=color, s=80, edgecolors=PAGE_BG, linewidths=1.2, label=name)
    for color, name in zip(COMMUNITY_COLORS, COMMUNITY_NAMES, strict=True)
]
leg = ax.legend(
    handles=legend_handles,
    loc="upper left",
    fontsize=8,
    title="Teams",
    title_fontsize=10,
    framealpha=0.95,
    fancybox=True,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_title().set_color(INK)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.text(
    0.5,
    0.01,
    f"50 nodes · {len(all_edges)} edges · node size ∝ degree · dashed = cross-team bridges",
    ha="center",
    va="bottom",
    fontsize=8,
    color=INK_MUTED,
)

fig.subplots_adjust(left=0.03, right=0.97, top=0.93, bottom=0.07)
plt.savefig(OUTPUT_DIR / f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
