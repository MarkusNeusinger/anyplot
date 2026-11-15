"""anyplot.ai
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
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint single-polarity ramp for edge weight: green (weak) to blue (strong)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

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

# Columns: set these to your labels
NODE = "Node"  # role: source
TARGET = "Connected node"  # role: target
WEIGHT = "Connection strength"  # role: weight

# Data: replace this block with your own labeled square matrix, for example
# df = pd.read_csv("adjacency.csv", index_col=0)  (rows and columns carry the same node names)
rng = np.random.default_rng(42)
communities = {
    "Research": [f"R{i:02d}" for i in range(1, 10)],
    "Marketing": [f"M{i:02d}" for i in range(1, 9)],
    "Engineering": [f"E{i:02d}" for i in range(1, 9)],
}
names = [name for members in communities.values() for name in members]
group_of = {name: group for group, members in communities.items() for name in members}
adj = np.zeros((len(names), len(names)))
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        if group_of[names[i]] == group_of[names[j]]:
            # within a department: dense, strong ties
            if rng.random() < 0.78:
                adj[i, j] = adj[j, i] = rng.uniform(0.5, 1.0)
        elif rng.random() < 0.12:
            # across departments: sparse, weak ties
            adj[i, j] = adj[j, i] = rng.uniform(0.08, 0.30)
df = pd.DataFrame(adj, index=pd.Index(names, name=NODE), columns=pd.Index(names, name=NODE))

# Plot: reads only df and the constants above
# Reorder nodes by hierarchical clustering so communities form diagonal blocks
size = min(df.shape)  # rows and columns are the same nodes in the same order
matrix = df.iloc[:size, :size].fillna(0)
matrix.columns = matrix.index
strength = matrix.to_numpy() / max(np.nanmax(matrix.to_numpy()), 1e-12)
dist = 1.0 - (strength + strength.T) / 2
np.fill_diagonal(dist, 0)
order = leaves_list(linkage(squareform(dist, checks=False), method="ward"))
ordered = matrix.iloc[order, order]

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)

sns.heatmap(
    ordered,
    mask=ordered == 0,  # absent edges show the page background, distinct from any weak edge
    cmap=imprint_seq,
    vmin=0,
    vmax=np.ceil(np.nanmax(ordered.to_numpy()) * 10) / 10,
    ax=ax,
    xticklabels=True,
    yticklabels=True,
    linewidths=0,
    square=True,
    cbar_kws={"shrink": 0.8, "pad": 0.02},
)

cbar = ax.collections[0].colorbar
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.set_label(WEIGHT, fontsize=10, color=INK)
cbar.outline.set_edgecolor(INK_SOFT)

ax.set_title("heatmap-adjacency · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=12)
ax.set_xlabel(NODE, fontsize=10, color=INK, labelpad=6)
ax.set_ylabel(TARGET, fontsize=10, color=INK, labelpad=6)
ax.tick_params(axis="both", labelsize=6.5, colors=INK_SOFT, length=2)
plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
plt.setp(ax.get_yticklabels(), rotation=0)

for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)

fig.subplots_adjust(left=0.1, right=0.95, top=0.93, bottom=0.12)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
