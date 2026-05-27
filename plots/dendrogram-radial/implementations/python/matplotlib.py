""" anyplot.ai
dendrogram-radial: Radial Dendrogram
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 81/100 | Created: 2026-05-14
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial.distance import pdist


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

family_names = ["Asteraceae", "Rosaceae", "Fabaceae", "Poaceae", "Lamiaceae"]
# Abbreviated species labels: As01-As10, Ro01-Ro10, Fa01-Fa10, Po01-Po10, La01-La10
prefixes = ["As", "Ro", "Fa", "Po", "La"]
species_labels = [f"{prefixes[i // 10]}{(i % 10) + 1:02d}" for i in range(50)]

# Data: morphological trait measurements for 50 plant species across 5 families
np.random.seed(42)
n_species = 50
n_traits = 12
k_families = 5
species_per_family = 10

family_centers = np.random.randn(k_families, n_traits) * 2.5
data = np.vstack([family_centers[f] + np.random.randn(species_per_family, n_traits) * 0.5 for f in range(k_families)])

# Hierarchical clustering (Ward linkage)
Z = linkage(pdist(data, metric="euclidean"), method="ward")
cluster_labels = fcluster(Z, k_families, criterion="maxclust")

# Build subtree cluster membership for branch coloring
node_cluster = {i: cluster_labels[i] for i in range(n_species)}
for i in range(len(Z)):
    left, right = int(Z[i, 0]), int(Z[i, 1])
    node_id = n_species + i
    lc = node_cluster.get(left, -1)
    rc = node_cluster.get(right, -1)
    node_cluster[node_id] = lc if lc == rc else -1


def link_color_func(node_id):
    c = node_cluster.get(node_id, -1)
    return IMPRINT[c - 1] if c != -1 else INK_SOFT


# Compute dendrogram layout with colored links
dendro = dendrogram(Z, no_plot=True, link_color_func=link_color_func)
icoord = np.array(dendro["icoord"])
dcoord = np.array(dendro["dcoord"])
link_colors = dendro["color_list"]
leaves = dendro["leaves"]

leaf_colors = [IMPRINT[cluster_labels[leaf] - 1] for leaf in leaves]

# Radial coordinate helpers — inner_r pads the root away from center
x_max = n_species * 10.0
max_d = float(dcoord.max())
outer_r = 1.0
inner_r = 0.18  # root converges here instead of the origin


def to_xy(x, y):
    theta = (x / x_max) * 2 * np.pi
    r = inner_r + (outer_r - inner_r) * (1.0 - y / max_d)
    return r * np.cos(theta), r * np.sin(theta)


# Plot
fig, ax = plt.subplots(figsize=(12, 12), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
ax.set_aspect("equal")

# Draw dendrogram branches
lw = 1.2
for i in range(len(icoord)):
    xs, ys = icoord[i], dcoord[i]
    color = link_colors[i]

    # Left vertical arm
    ax0, ay0 = to_xy(xs[0], ys[0])
    ax1, ay1 = to_xy(xs[1], ys[1])
    ax.plot([ax0, ax1], [ay0, ay1], color=color, linewidth=lw, solid_capstyle="round")

    # Arc at merge height (constant radius, sweep angle)
    theta1 = (xs[1] / x_max) * 2 * np.pi
    theta2 = (xs[2] / x_max) * 2 * np.pi
    r_merge = inner_r + (outer_r - inner_r) * (1.0 - ys[1] / max_d)
    arc_angles = np.linspace(theta1, theta2, 80)
    ax.plot(r_merge * np.cos(arc_angles), r_merge * np.sin(arc_angles), color=color, linewidth=lw)

    # Right vertical arm
    ax2, ay2 = to_xy(xs[2], ys[2])
    ax3, ay3 = to_xy(xs[3], ys[3])
    ax.plot([ax2, ax3], [ay2, ay3], color=color, linewidth=lw, solid_capstyle="round")

# Leaf markers and circumference labels
label_r = outer_r + 0.07
for j in range(n_species):
    theta = ((5.0 + j * 10.0) / x_max) * 2 * np.pi
    ax.scatter(outer_r * np.cos(theta), outer_r * np.sin(theta), color=leaf_colors[j], s=110, zorder=5, linewidths=0)

    theta_deg = np.degrees(theta)
    lx = label_r * np.cos(theta)
    ly = label_r * np.sin(theta)
    # Flip labels on the left half so they read outward in both halves
    if np.cos(theta) >= 0:
        ha, rotation = "left", theta_deg
    else:
        ha, rotation = "right", theta_deg - 180
    ax.text(
        lx,
        ly,
        species_labels[leaves[j]],
        fontsize=6,
        color=INK_SOFT,
        rotation=rotation,
        rotation_mode="anchor",
        ha=ha,
        va="center",
    )

# Style
ax.set_xlim(-1.6, 1.6)
ax.set_ylim(-1.6, 1.6)
ax.axis("off")

ax.set_title("dendrogram-radial · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=16)

# Legend
legend_elements = [
    Line2D([0], [0], marker="o", linestyle="None", markerfacecolor=IMPRINT[i], markersize=14, label=family_names[i])
    for i in range(k_families)
]
leg = ax.legend(
    handles=legend_elements,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.06),
    ncol=k_families,
    fontsize=16,
    frameon=True,
    handletextpad=0.4,
    columnspacing=1.0,
)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
