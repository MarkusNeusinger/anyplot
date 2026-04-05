"""pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 84/100 | Updated: 2026-04-05
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import FancyBboxPatch
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage


# Style - leverage seaborn's distinctive theming
sns.set_theme(style="white", rc={"axes.linewidth": 0.8, "font.family": "sans-serif"})
sns.set_context("talk", font_scale=1.2)

# Custom palette starting with Python Blue
species_palette = ["#306998", "#E8843C", "#4EA86B"]
species_colors = dict(zip(["Setosa", "Versicolor", "Virginica"], species_palette, strict=True))

# Data - use seaborn's iris dataset (30 samples for readable dendrogram)
np.random.seed(42)
iris = sns.load_dataset("iris")
samples = (
    iris.groupby("species").apply(lambda g: g.sample(10, random_state=42), include_groups=False).reset_index(level=0)
)

features = samples[["sepal_length", "sepal_width", "petal_length", "petal_width"]].values

# Build labels: Species-Number
counters = dict.fromkeys(["setosa", "versicolor", "virginica"], 0)
labels = []
species_list = []
for species in samples["species"]:
    counters[species] += 1
    labels.append(f"{species.title()}-{counters[species]}")
    species_list.append(species.title())

# Compute linkage
linkage_matrix = linkage(features, method="ward")

# Find optimal threshold that separates Setosa from others
# Use fcluster to identify the 2-cluster split
clusters_2 = fcluster(linkage_matrix, t=2, criterion="maxclust")
# The threshold is the distance of the second-to-last merge (2 clusters → 1)
threshold_distance = linkage_matrix[-2, 2]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Use a single muted color for all branches, letting annotations tell the story
dn = dendrogram(
    linkage_matrix,
    labels=labels,
    leaf_rotation=45,
    leaf_font_size=16,
    ax=ax,
    above_threshold_color="#888888",
    color_threshold=threshold_distance * 0.95,
    link_color_func=lambda k: "#888888",
)

# Color each branch segment by which cluster its leaves belong to
# Recolor: walk the dendrogram and color branches by species membership
icoord = np.array(dn["icoord"])
dcoord = np.array(dn["dcoord"])
leaf_positions = {label: x for x, label in zip(dn["leaves"], range(len(dn["leaves"])), strict=True)}

# Map each leaf to its species color
leaf_label_map = {}
for i, lbl in enumerate(dn["ivl"]):
    sp = lbl.rsplit("-", 1)[0]
    leaf_label_map[i] = species_colors.get(sp, "#888888")

# Color x-axis labels by species with larger font
for lbl in ax.get_xticklabels():
    species = lbl.get_text().rsplit("-", 1)[0]
    if species in species_colors:
        lbl.set_color(species_colors[species])
        lbl.set_fontweight("bold")
        lbl.set_fontsize(16)

# Add horizontal threshold line for storytelling
ax.axhline(y=threshold_distance, color="#CC4455", linewidth=1.5, linestyle="--", alpha=0.6, zorder=1)

# Annotate the threshold line
ax.text(
    0.98,
    threshold_distance + 0.3,
    f"Major split (d = {threshold_distance:.1f})",
    transform=ax.get_yaxis_transform(),
    fontsize=13,
    color="#CC4455",
    ha="right",
    va="bottom",
    fontstyle="italic",
)

# Add subtle background shading for the two main clusters
# Find x-boundaries for Setosa cluster (left) vs Versicolor/Virginica (right)
x_labels = dn["ivl"]
setosa_indices = [i for i, lbl in enumerate(x_labels) if "Setosa" in lbl]
other_indices = [i for i, lbl in enumerate(x_labels) if "Setosa" not in lbl]

if setosa_indices and other_indices:
    # x positions in dendrogram are at 5, 15, 25, ... (step of 10)
    setosa_x_min = min(setosa_indices) * 10
    setosa_x_max = max(setosa_indices) * 10 + 10
    other_x_min = min(other_indices) * 10
    other_x_max = max(other_indices) * 10 + 10

    y_max = ax.get_ylim()[1]

    # Subtle shading for Setosa cluster
    setosa_rect = FancyBboxPatch(
        (setosa_x_min - 3, -0.2),
        setosa_x_max - setosa_x_min + 6,
        threshold_distance + 0.2,
        boxstyle="round,pad=1",
        facecolor=species_colors["Setosa"],
        alpha=0.04,
        edgecolor="none",
        zorder=0,
    )
    ax.add_patch(setosa_rect)

    # Subtle shading for Versicolor/Virginica cluster
    other_rect = FancyBboxPatch(
        (other_x_min - 3, -0.2),
        other_x_max - other_x_min + 6,
        threshold_distance + 0.2,
        boxstyle="round,pad=1",
        facecolor=species_colors["Versicolor"],
        alpha=0.04,
        edgecolor="none",
        zorder=0,
    )
    ax.add_patch(other_rect)

    # Cluster annotations
    setosa_center = (setosa_x_min + setosa_x_max) / 2
    ax.text(
        setosa_center,
        threshold_distance * 0.75,
        "Setosa\n(well-separated)",
        fontsize=13,
        ha="center",
        va="center",
        color=species_colors["Setosa"],
        fontweight="bold",
        alpha=0.7,
    )

    other_center = (other_x_min + other_x_max) / 2
    ax.text(
        other_center,
        threshold_distance * 0.75,
        "Versicolor + Virginica\n(overlapping species)",
        fontsize=13,
        ha="center",
        va="center",
        color=species_colors["Versicolor"],
        fontweight="bold",
        alpha=0.7,
    )

# Axes and title
ax.set_xlabel("Iris Samples (by Species)", fontsize=20)
ax.set_ylabel("Distance (Ward Linkage)", fontsize=20)
ax.set_title("dendrogram-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="y", labelsize=16)

# Grid and spines - seaborn distinctive styling
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color="#cccccc")
ax.set_axisbelow(True)
sns.despine(ax=ax)

# Legend for x-axis label colors (not branch colors)
for name, color in species_colors.items():
    ax.scatter([], [], c=[color], s=150, label=name, marker="s")
ax.legend(
    title="Species (label color)",
    loc="upper right",
    fontsize=14,
    title_fontsize=15,
    framealpha=0.95,
    edgecolor="#cccccc",
    fancybox=True,
    shadow=False,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
