""" anyplot.ai
heatmap-adjacency: Network Adjacency Matrix Heatmap
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 85/100 | Created: 2026-05-08
"""

import os
import sys


# Fix sys.path to avoid importing local seaborn.py / matplotlib.py instead of the libraries
if sys.path and sys.path[0] == os.path.dirname(__file__):
    sys.path.pop(0)

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

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

# Data — corporate social network with 3 departments
np.random.seed(42)

communities = {
    "Research": [f"R{i:02d}" for i in range(1, 10)],
    "Marketing": [f"M{i:02d}" for i in range(1, 9)],
    "Engineering": [f"E{i:02d}" for i in range(1, 9)],
}
nodes = [n for group in communities.values() for n in group]
n = len(nodes)
node_idx = {name: i for i, name in enumerate(nodes)}

adj = np.zeros((n, n))

# Within-community: dense, high-weight connections
for group_nodes in communities.values():
    members = list(group_nodes)
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            if np.random.rand() < 0.78:
                w = np.random.uniform(0.5, 1.0)
                u, v = node_idx[members[i]], node_idx[members[j]]
                adj[u, v] = adj[v, u] = w

# Cross-community: sparse, low-weight connections
group_list = list(communities.values())
for gi in range(len(group_list)):
    for gj in range(gi + 1, len(group_list)):
        for u_name in group_list[gi]:
            for v_name in group_list[gj]:
                if np.random.rand() < 0.12:
                    w = np.random.uniform(0.08, 0.30)
                    u, v = node_idx[u_name], node_idx[v_name]
                    adj[u, v] = adj[v, u] = w

# Reorder nodes by hierarchical clustering to expose block-diagonal structure
dist = 1.0 - adj
np.fill_diagonal(dist, 0)
condensed = squareform(dist)
Z = linkage(condensed, method="ward")
order = leaves_list(Z)
nodes_ordered = [nodes[i] for i in order]
adj_ordered = adj[np.ix_(order, order)]

# Plot
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)

mask = adj_ordered == 0

sns.heatmap(
    adj_ordered,
    mask=mask,
    cmap="viridis",
    vmin=0,
    vmax=1.0,
    ax=ax,
    xticklabels=nodes_ordered,
    yticklabels=nodes_ordered,
    linewidths=0,
    square=True,
    cbar_kws={"label": "Connection Strength", "shrink": 0.75, "pad": 0.02},
)

# Style colorbar
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=14, colors=INK_SOFT)
cbar.set_label("Connection Strength", fontsize=16, color=INK)
cbar.outline.set_edgecolor(INK_SOFT)

# Labels and title
ax.set_xlabel("Node", fontsize=20, color=INK, labelpad=12)
ax.set_ylabel("Node", fontsize=20, color=INK, labelpad=12)
ax.set_title("heatmap-adjacency · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)

ax.tick_params(axis="both", labelsize=11, colors=INK_SOFT)
ax.tick_params(axis="x", rotation=45)
ax.tick_params(axis="y", rotation=0)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
