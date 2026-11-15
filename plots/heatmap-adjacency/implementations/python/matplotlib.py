"""anyplot.ai
heatmap-adjacency: Network Adjacency Matrix Heatmap
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.transforms import blended_transform_factory


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per community in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])
imprint_seq.set_bad(PAGE_BG)  # absent edges take the page tone

# Columns: the matrix is the table, only the color bar needs a name
SOURCE = "Source node (sorted by community)"  # role: source
TARGET = "Target node (sorted by community)"  # role: target
WEIGHT = "Connection strength"  # role: weight

# Data: replace this block with your own labeled square matrix, for example df = pd.read_csv("edges.csv", index_col=0)
# Research collaboration network; node labels start with the community, nodes are sorted by community
np.random.seed(42)
communities = {"Neuro": 10, "CS": 12, "Psych": 8}
labels = [f"{name} {k:02d}" for name, size in communities.items() for k in range(1, size + 1)]
group = np.repeat(list(communities), list(communities.values()))
same = group[:, None] == group[None, :]
present = np.triu(np.random.random((len(labels), len(labels))) < np.where(same, 0.72, 0.12), k=1)
strength = np.where(same, np.random.uniform(0.5, 1.0, same.shape), np.random.uniform(0.05, 0.3, same.shape))
upper = np.where(present, strength, 0.0)
df = pd.DataFrame(upper + upper.T, index=labels, columns=labels)

# Plot: reads only df and the constants above
matrix = df.to_numpy()
nodes = [str(node) for node in df.index]
groups = pd.Series([node.split()[0] for node in nodes])
sizes = groups.groupby(groups, sort=False).size()
edges = np.concatenate([[0], np.cumsum(sizes.to_numpy())])

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG, layout="constrained")
ax.set_facecolor(PAGE_BG)
im = ax.imshow(
    np.where(matrix == 0, np.nan, matrix), cmap=imprint_seq, vmin=0, vmax=np.nanmax(matrix), interpolation="nearest"
)

# Community boundary lines
for b in edges[1:-1]:
    ax.axhline(b - 0.5, color=INK, linewidth=1.2, alpha=0.5)
    ax.axvline(b - 0.5, color=INK, linewidth=1.2, alpha=0.5)

# Community names above the matrix: data x, axes y
trans = blended_transform_factory(ax.transData, ax.transAxes)
for i, name in enumerate(sizes.index):
    ax.text(
        (edges[i] + edges[i + 1] - 1) / 2,
        1.01,
        name,
        transform=trans,
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
    )

# Style
ax.set_xticks(range(len(nodes)), nodes, rotation=90, fontsize=6.5, color=INK_SOFT)
ax.set_yticks(range(len(nodes)), nodes, fontsize=6.5, color=INK_SOFT)
ax.tick_params(length=0, pad=2)
for spine in ax.spines.values():
    spine.set_edgecolor(INK_SOFT)
    spine.set_linewidth(0.8)
ax.set_xlabel(TARGET, fontsize=10, color=INK)
ax.set_ylabel(SOURCE, fontsize=10, color=INK)
ax.set_title(
    "heatmap-adjacency · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK, pad=24
)

cbar = fig.colorbar(im, ax=ax, shrink=0.75, pad=0.02)
cbar.set_label(WEIGHT, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, labelcolor=INK_SOFT, color=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
