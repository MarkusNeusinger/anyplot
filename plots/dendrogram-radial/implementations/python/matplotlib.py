"""anyplot.ai
dendrogram-radial: Radial Dendrogram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per cluster in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
INNER_RADIUS = 0.18  # the root converges here instead of the origin
OUTER_RADIUS = 1.0  # leaves sit on this circle

N_CLUSTERS = 5  # the tree is cut into this many clusters, which get the branch colors
CLUSTER = "Cluster"  # legend title

# Data: replace this block with your own table, for example df = pd.read_csv("traits.csv", index_col=0)
# A labeled matrix: one row per leaf (the row labels name the leaves), numeric measurement columns.
rng = np.random.default_rng(42)
prefixes = ["As", "Ro", "Fa", "Po", "La"]
per_group = 10
n_traits = 12
centers = rng.standard_normal((len(prefixes), n_traits)) * 2.5
measurements = np.vstack([c + rng.standard_normal((per_group, n_traits)) * 0.5 for c in centers])
df = pd.DataFrame(
    measurements,
    index=[f"{p}{k + 1:02d}" for p in prefixes for k in range(per_group)],
    columns=[f"Trait {t:02d}" for t in range(1, n_traits + 1)],
)

# Plot: reads only df and the constants above
n_leaves = len(df)

# Ward linkage on the measurements; branch color = the cluster a whole subtree belongs to
Z = linkage(df.to_numpy(dtype=float), method="ward")
cluster_of = fcluster(Z, N_CLUSTERS, criterion="maxclust")
groups = [f"{CLUSTER} {c}" for c in range(1, cluster_of.max() + 1)]
group_color = {g: IMPRINT_PALETTE[i] for i, g in enumerate(groups)}
node_group = {i: groups[cluster_of[i] - 1] for i in range(n_leaves)}
for i, (left, right) in enumerate(Z[:, :2].astype(int)):
    lg, rg = node_group[left], node_group[right]
    node_group[n_leaves + i] = lg if lg == rg else None


def link_color_func(node_id):
    g = node_group[node_id]
    return group_color[g] if g is not None else INK_SOFT


tree = dendrogram(Z, no_plot=True, link_color_func=link_color_func)
icoord = np.array(tree["icoord"])
dcoord = np.array(tree["dcoord"])
leaves = tree["leaves"]

x_max = n_leaves * 10.0
max_d = dcoord.max()


def radius(d):
    return INNER_RADIUS + (OUTER_RADIUS - INNER_RADIUS) * (1.0 - d / max_d)


def angle(x):
    return x / x_max * 2 * np.pi


fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")

# Branches: two radial arms joined by an arc at the merge radius
for xs, ys, color in zip(icoord, dcoord, tree["color_list"], strict=True):
    for x, y0, y1 in ((xs[0], ys[0], ys[1]), (xs[2], ys[3], ys[2])):
        ax.plot(
            [radius(y0) * np.cos(angle(x)), radius(y1) * np.cos(angle(x))],
            [radius(y0) * np.sin(angle(x)), radius(y1) * np.sin(angle(x))],
            color=color,
            linewidth=1.6,
            solid_capstyle="round",
        )
    arc = np.linspace(angle(xs[1]), angle(xs[2]), 80)
    ax.plot(radius(ys[1]) * np.cos(arc), radius(ys[1]) * np.sin(arc), color=color, linewidth=1.6)

# Leaf markers and labels around the circumference
label_radius = OUTER_RADIUS + 0.05
for j, leaf in enumerate(leaves):
    theta = angle(5.0 + j * 10.0)
    ax.scatter(
        OUTER_RADIUS * np.cos(theta),
        OUTER_RADIUS * np.sin(theta),
        color=group_color[groups[cluster_of[leaf] - 1]],
        s=28,
        zorder=5,
        linewidths=0,
    )
    flip = np.cos(theta) < 0  # keep labels upright on the left half
    ax.text(
        label_radius * np.cos(theta),
        label_radius * np.sin(theta),
        df.index[leaf],
        fontsize=7,
        color=INK_SOFT,
        rotation=np.degrees(theta) - (180 if flip else 0),
        rotation_mode="anchor",
        ha="right" if flip else "left",
        va="center",
    )

# Style
ax.set_xlim(-1.3, 1.3)
ax.set_ylim(-1.3, 1.3)
ax.axis("off")
ax.set_title("dendrogram-radial · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)

handles = [
    Line2D([0], [0], marker="o", linestyle="None", markerfacecolor=group_color[g], markeredgewidth=0, markersize=7)
    for g in groups
]
leg = fig.legend(
    handles,
    groups,
    title=CLUSTER,
    loc="lower center",
    bbox_to_anchor=(0.5, 0.012),
    ncol=len(groups),
    fontsize=8,
    title_fontsize=8,
    frameon=True,
    handletextpad=0.3,
    columnspacing=1.0,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.11)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
