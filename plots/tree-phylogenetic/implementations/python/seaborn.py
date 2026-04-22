""" pyplots.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import Patch
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform


# Set seaborn style for better aesthetics
sns.set_theme(style="white")

# Define primate species for phylogenetic tree
species = ["Human", "Chimpanzee", "Gorilla", "Orangutan", "Gibbon", "Baboon", "Macaque", "Marmoset", "Lemur", "Tarsier"]

# Create evolutionary distance matrix (symmetric)
# Based on approximate mitochondrial DNA divergence (millions of years ago)
np.random.seed(42)
n_species = len(species)

# Base distances representing evolutionary divergence
# Closer species have smaller distances
base_distances = np.array(
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

# Convert distance matrix to condensed form for hierarchical clustering
condensed_distances = squareform(base_distances)

# Perform hierarchical clustering using UPGMA (average linkage)
# This is commonly used for phylogenetic analysis
linkage_matrix = linkage(condensed_distances, method="average")

# Create figure with seaborn styling
fig, ax = plt.subplots(figsize=(16, 9))

# Define colors using Python palette and colorblind-safe colors
# Assign each species to a clade index for consistent coloring
clade_colors = {
    "Human": "#306998",  # Python Blue - Great Apes
    "Chimpanzee": "#306998",
    "Gorilla": "#306998",
    "Orangutan": "#4A90D9",  # Light blue - Asian great ape
    "Gibbon": "#4A90D9",
    "Baboon": "#FFD43B",  # Python Yellow - Old World Monkeys
    "Macaque": "#FFD43B",
    "Marmoset": "#2ECC71",  # Green - New World Monkey
    "Lemur": "#E74C3C",  # Red - Prosimians
    "Tarsier": "#E74C3C",
}

# Define link colors based on cluster membership
# Map each leaf to its clade color for dendrogram branches
leaf_colors = [clade_colors[s] for s in species]

# Create a color mapping function for dendrogram links
# Links below leaves inherit the leaf color, higher links use a neutral color
n = len(species)


def get_link_color(link_id):
    """Return color for dendrogram link based on cluster composition."""
    if link_id < n:
        return leaf_colors[link_id]
    # For internal nodes, get the cluster members
    cluster_idx = int(link_id - n)
    left_child = int(linkage_matrix[cluster_idx, 0])
    right_child = int(linkage_matrix[cluster_idx, 1])

    # Get colors of both children
    left_color = get_link_color(left_child)
    right_color = get_link_color(right_child)

    # If both children have same color, use that color
    if left_color == right_color:
        return left_color
    # Otherwise use neutral gray for mixed clades
    return "#808080"


# Build link color list for all links in dendrogram
link_colors = [get_link_color(i + n) for i in range(len(linkage_matrix))]

# Plot dendrogram (phylogenetic tree) with custom clade colors
dendro = dendrogram(
    linkage_matrix,
    labels=species,
    orientation="left",
    ax=ax,
    leaf_font_size=18,
    link_color_func=lambda k: link_colors[k - n] if k >= n else leaf_colors[k],
)

# Make branch lines thicker for improved visibility
for line_collection in ax.collections:
    line_collection.set_linewidth(3)

# Style the dendrogram with seaborn aesthetics
ax.set_xlabel("Evolutionary Distance (Million Years)", fontsize=20, fontweight="bold")
ax.set_title("Primate Evolution · tree-phylogenetic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Adjust tick parameters for readability
ax.tick_params(axis="x", labelsize=16)
ax.tick_params(axis="y", labelsize=18)

# Add subtle grid on x-axis only
ax.grid(axis="x", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Add scale bar annotation
ax.annotate(
    "Scale: branch length = evolutionary distance",
    xy=(0.98, 0.02),
    xycoords="axes fraction",
    fontsize=14,
    ha="right",
    va="bottom",
    style="italic",
    color="#666666",
)

# Color the species labels based on clade
for label in ax.get_yticklabels():
    species_name = label.get_text()
    if species_name in clade_colors:
        label.set_color(clade_colors[species_name])
        label.set_fontweight("bold")

# Add legend for clades (positioned to avoid overlap)
legend_elements = [
    Patch(facecolor="#306998", edgecolor="none", label="Great Apes"),
    Patch(facecolor="#4A90D9", edgecolor="none", label="Lesser Apes"),
    Patch(facecolor="#FFD43B", edgecolor="none", label="Old World Monkeys"),
    Patch(facecolor="#2ECC71", edgecolor="none", label="New World Monkeys"),
    Patch(facecolor="#E74C3C", edgecolor="none", label="Prosimians"),
]
ax.legend(handles=legend_elements, loc="lower left", fontsize=14, title="Clades", title_fontsize=16, framealpha=0.9)

# Remove top and right spines for cleaner look
sns.despine(ax=ax, top=True, right=True)

# Adjust layout
plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
