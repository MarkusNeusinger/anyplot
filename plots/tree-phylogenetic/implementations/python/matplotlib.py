""" anyplot.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: matplotlib 3.11.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per clade in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
NODE = "Node"  # role: species_names
PARENT = "Parent"  # role: extra
BRANCH_LENGTH = "Branch length (substitutions per site)"  # role: branch_lengths
CLADE = "Clade"  # role: extra

# Data: replace this block with your own edge list, for example df = pd.read_csv("tree.csv")
# One row per node: its parent (empty for the root), the length of the branch above it,
# and the clade that colors that branch (empty for branches outside every clade).
# Primate phylogeny from mitochondrial DNA; children are listed in drawing order, bottom to top.
df = pd.DataFrame(
    [
        ("Primates", None, 0.05, None),
        ("Prosimians", "Primates", 0.03, "Prosimians"),
        ("Lorisoids", "Prosimians", 0.02, "Prosimians"),
        ("Galago", "Lorisoids", 0.14, "Prosimians"),
        ("Tarsier", "Lorisoids", 0.14, "Prosimians"),
        ("Lemur", "Prosimians", 0.10, "Prosimians"),
        ("Simians", "Primates", 0.03, None),
        ("Monkeys", "Simians", 0.04, "Monkeys"),
        ("New World Monkeys", "Monkeys", 0.03, "Monkeys"),
        ("Spider Monkey", "New World Monkeys", 0.05, "Monkeys"),
        ("Capuchin", "New World Monkeys", 0.04, "Monkeys"),
        ("Old World Monkeys", "Monkeys", 0.02, "Monkeys"),
        ("Baboon", "Old World Monkeys", 0.04, "Monkeys"),
        ("Rhesus Macaque", "Old World Monkeys", 0.04, "Monkeys"),
        ("Apes", "Simians", 0.02, "Apes"),
        ("Asian Apes", "Apes", 0.03, "Apes"),
        ("Gibbon", "Asian Apes", 0.03, "Apes"),
        ("Orangutan", "Asian Apes", 0.02, "Apes"),
        ("African Apes", "Apes", 0.01, "Apes"),
        ("Gorilla", "African Apes", 0.03, "Apes"),
        ("Hominini", "African Apes", 0.01, "Apes"),
        ("Chimpanzee", "Hominini", 0.01, "Apes"),
        ("Human", "Hominini", 0.01, "Apes"),
    ],
    columns=[NODE, PARENT, BRANCH_LENGTH, CLADE],
)

# Plot: reads only df and the constants above
nodes = df[NODE].tolist()
parents = dict(zip(df[NODE], df[PARENT], strict=True))
lengths = dict(zip(df[NODE], df[BRANCH_LENGTH], strict=True))
clades = dict(zip(df[NODE], df[CLADE], strict=True))
children = {node: df.loc[df[PARENT] == node, NODE].tolist() for node in nodes}
root = next(node for node in nodes if pd.isna(parents[node]))
clade_names = df[CLADE].dropna().unique().tolist()
clade_colors = {clade: IMPRINT_PALETTE[i] for i, clade in enumerate(clade_names)}

# Rectangular layout: x is the distance from the root (a root without a stem starts at 0),
# tips sit one row apart in preorder, and every internal node sits midway between its outer children
x_pos, y_pos, preorder, stack = {}, {}, [], [root]
while stack:
    node = stack.pop()
    preorder.append(node)
    parent = parents[node]
    start = 0.0 if pd.isna(parent) else x_pos[parent]
    x_pos[node] = start + (0.0 if pd.isna(lengths[node]) else lengths[node])
    stack.extend(reversed(children[node]))
tips = [node for node in preorder if not children[node]]
y_pos.update({tip: float(rank) for rank, tip in enumerate(tips)})
for node in reversed(preorder):
    if children[node]:
        y_pos[node] = (y_pos[children[node][0]] + y_pos[children[node][-1]]) / 2

# Branch segments: a horizontal per node (its own length) and a vertical joining each node's children
horizontal, horizontal_colors, vertical, vertical_colors = [], [], [], []
for node in preorder:
    color = clade_colors.get(clades[node], INK_SOFT)
    start = 0.0 if pd.isna(parents[node]) else x_pos[parents[node]]
    horizontal.append([(start, y_pos[node]), (x_pos[node], y_pos[node])])
    horizontal_colors.append(color)
    if children[node]:
        ys = [y_pos[c] for c in children[node]]
        vertical.append([(x_pos[node], min(ys)), (x_pos[node], max(ys))])
        vertical_colors.append(color)

depth = max(x_pos.values())
tip_x = np.array([x_pos[tip] for tip in tips])
tip_y = np.array([y_pos[tip] for tip in tips])
tip_colors = [clade_colors.get(clades[tip], INK_SOFT) for tip in tips]

# Scale bar: the largest 1-2-5 step that fits in a quarter of the tree depth
magnitude = 10 ** np.floor(np.log10(depth / 4))
scale = max(step * magnitude for step in (1, 2, 5) if step * magnitude <= depth / 4)
scale_y = -0.9

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

ax.add_collection(LineCollection(vertical, colors=vertical_colors, linewidths=2.0, capstyle="round", zorder=2))
ax.add_collection(LineCollection(horizontal, colors=horizontal_colors, linewidths=2.0, capstyle="round", zorder=2))
ax.scatter(tip_x, tip_y, s=28, color=tip_colors, edgecolors=PAGE_BG, linewidths=0.8, zorder=3)
for tip, x, y in zip(tips, tip_x, tip_y, strict=True):
    ax.annotate(tip, (x, y), xytext=(6, 0), textcoords="offset points", va="center", ha="left", fontsize=8, color=INK)

# Scale bar, drawn in the same data units as the branches
ax.plot([0, scale], [scale_y, scale_y], color=INK, linewidth=2.0, solid_capstyle="butt")
ax.annotate(
    f"{scale:g} substitutions per site",
    (scale, scale_y),
    xytext=(6, 0),
    textcoords="offset points",
    va="center",
    ha="left",
    fontsize=7,
    color=INK_SOFT,
)

# Style
title = "tree-phylogenetic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)
ax.set_xlabel(BRANCH_LENGTH, fontsize=10, color=INK)
ax.set_xlim(-depth * 0.03, depth * 1.32)
ax.set_ylim(scale_y - 0.7, len(tips) - 0.4)
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.tick_params(axis="y", left=False, labelleft=False)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)

legend_handles = [Patch(facecolor=clade_colors[clade], edgecolor="none", label=clade) for clade in clade_names]
leg = ax.legend(handles=legend_handles, title=CLADE, loc="upper right", fontsize=8, title_fontsize=8, frameon=True)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.8)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK)

fig.subplots_adjust(left=0.04, right=0.97, top=0.91, bottom=0.12)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
