""" anyplot.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: seaborn 0.13.2 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-21
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per clade in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
SPECIES = "Species"  # role: species_names
CLADE = "Clade"  # role: extra
PARTNER = "Compared with"  # role: extra
DISTANCE = "Evolutionary distance (million years)"  # role: branch_lengths

# Data: replace this block with your own table, for example df = pd.read_csv("distances.csv")
# One row per pair of species: the pairwise divergence (approximate mitochondrial DNA, million years)
species_order = [
    "Human",
    "Chimpanzee",
    "Gorilla",
    "Orangutan",
    "Gibbon",
    "Baboon",
    "Macaque",
    "Marmoset",
    "Lemur",
    "Tarsier",
]
clade_of = {
    "Human": "Great Apes",
    "Chimpanzee": "Great Apes",
    "Gorilla": "Great Apes",
    "Orangutan": "Lesser Apes",
    "Gibbon": "Lesser Apes",
    "Baboon": "Old World Monkeys",
    "Macaque": "Old World Monkeys",
    "Marmoset": "New World Monkeys",
    "Lemur": "Prosimians",
    "Tarsier": "Prosimians",
}
pairwise = np.array(
    [
        [0, 6, 9, 14, 18, 25, 25, 35, 55, 58],  # Human
        [6, 0, 9, 14, 18, 25, 25, 35, 55, 58],  # Chimpanzee
        [9, 9, 0, 14, 18, 25, 25, 35, 55, 58],  # Gorilla
        [14, 14, 14, 0, 18, 25, 25, 35, 55, 58],  # Orangutan
        [18, 18, 18, 18, 0, 25, 25, 35, 55, 58],  # Gibbon
        [25, 25, 25, 25, 25, 0, 10, 35, 55, 58],  # Baboon
        [25, 25, 25, 25, 25, 10, 0, 35, 55, 58],  # Macaque
        [35, 35, 35, 35, 35, 35, 35, 0, 55, 58],  # Marmoset
        [55, 55, 55, 55, 55, 55, 55, 55, 0, 50],  # Lemur
        [58, 58, 58, 58, 58, 58, 58, 58, 50, 0],  # Tarsier
    ]
)
df = pd.DataFrame(
    {
        SPECIES: np.repeat(species_order, len(species_order)),
        CLADE: [clade_of[s] for s in np.repeat(species_order, len(species_order))],
        PARTNER: species_order * len(species_order),
        DISTANCE: pairwise.ravel(),
    }
)

# Plot: reads only df and the constants above
species = list(df[SPECIES].unique())
matrix = df.pivot_table(index=SPECIES, columns=PARTNER, values=DISTANCE, sort=False).loc[species, species]
species_clade = df.drop_duplicates(SPECIES).set_index(SPECIES)[CLADE]
clades = list(species_clade.unique())
clade_color = {clade: IMPRINT_PALETTE[i] for i, clade in enumerate(clades)}
leaf_colors = [clade_color[species_clade[s]] for s in species]
n = len(species)

# UPGMA tree from the pairwise distances
linkage_matrix = linkage(squareform(matrix.to_numpy(dtype=float), checks=False), method="average")

# A branch takes its clade's color when everything below it belongs to that clade, else the neutral ink
node_colors = list(leaf_colors)
for left, right, _, _ in linkage_matrix:
    left_color, right_color = node_colors[int(left)], node_colors[int(right)]
    node_colors.append(left_color if left_color == right_color else INK_SOFT)

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

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

dendrogram(
    linkage_matrix,
    labels=species,
    orientation="left",
    ax=ax,
    leaf_font_size=10,
    link_color_func=lambda k: node_colors[k],
)
for branches in ax.collections:
    branches.set_linewidth(1.8)

# Style
ax.set_xlabel(DISTANCE, fontsize=10, fontweight="bold", color=INK)
ax.set_title("tree-phylogenetic · python · seaborn · anyplot.ai", fontsize=12, fontweight="bold", pad=10, color=INK)
ax.tick_params(axis="x", labelsize=8, colors=INK_SOFT)
ax.tick_params(axis="y", labelsize=9, colors=INK_SOFT)
ax.grid(axis="x", alpha=0.15, linestyle="-", linewidth=0.5, color=INK_SOFT)
ax.set_axisbelow(True)

ax.annotate(
    "Scale: branch length = evolutionary distance",
    xy=(0.02, 0.03),
    xycoords="axes fraction",
    fontsize=7,
    ha="left",
    va="bottom",
    style="italic",
    color=INK_SOFT,
)

# Tip labels take their clade's color
for label in ax.get_yticklabels():
    label.set_color(clade_color[species_clade[label.get_text()]])
    label.set_fontweight("bold")

ax.legend(
    handles=[Patch(facecolor=clade_color[clade], edgecolor="none", label=clade) for clade in clades],
    loc="center left",
    bbox_to_anchor=(0.2, 0.5),
    fontsize=7,
    title=CLADE,
    title_fontsize=8,
    framealpha=0.9,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)

sns.despine(ax=ax, top=True, right=True)
fig.subplots_adjust(left=0.12, right=0.84, top=0.9, bottom=0.14)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
