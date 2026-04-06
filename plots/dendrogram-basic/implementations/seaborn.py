""" pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 89/100 | Updated: 2026-04-05
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Style - leverage seaborn's distinctive theming
sns.set_theme(style="white", rc={"axes.linewidth": 0.8, "font.family": "sans-serif"})
sns.set_context("talk", font_scale=1.2)

# Custom palette starting with Python Blue
species_palette = sns.color_palette(["#306998", "#E8843C", "#4EA86B"])
species_names = ["Setosa", "Versicolor", "Virginica"]
species_colors = dict(zip(species_names, species_palette, strict=True))

# Data - use seaborn's iris dataset (30 samples for readable dendrogram)
np.random.seed(42)
iris = sns.load_dataset("iris")
samples = (
    iris.groupby("species").apply(lambda g: g.sample(10, random_state=42), include_groups=False).reset_index(level=0)
)

feature_cols = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
features = samples[feature_cols].copy()

# Build sample labels: Species-Number
counters = dict.fromkeys(["setosa", "versicolor", "virginica"], 0)
labels = []
species_list = []
for species in samples["species"]:
    counters[species] += 1
    labels.append(f"{species.title()}-{counters[species]}")
    species_list.append(species.title())

features.index = labels

# Rename columns to readable format
features.columns = ["Sepal Length", "Sepal Width", "Petal Length", "Petal Width"]

# Row colors by species - seaborn distinctive feature for annotating clusters
row_colors = pd.Series([species_colors[sp] for sp in species_list], index=labels, name="Species")

# sns.clustermap - seaborn's distinctive hierarchical clustering + dendrogram
# This IS the idiomatic seaborn way to visualize dendrograms with data context
g = sns.clustermap(
    features,
    method="ward",
    row_colors=row_colors,
    col_cluster=True,
    cmap=sns.color_palette("viridis", as_cmap=True),
    figsize=(16, 9),
    dendrogram_ratio=(0.25, 0.12),
    linewidths=0.5,
    linecolor="white",
    cbar_kws={"label": "Feature Value"},
    tree_kws={"linewidths": 1.8, "colors": "#666666"},
    xticklabels=True,
    yticklabels=True,
)

# Customize the row dendrogram (main dendrogram showing sample clustering)
row_dendro_ax = g.ax_row_dendrogram
row_dendro_ax.set_xlabel("Distance (Ward)", fontsize=14)

# Customize heatmap axis labels
g.ax_heatmap.set_xlabel("Iris Features", fontsize=20)
g.ax_heatmap.set_ylabel("Iris Samples (by Species)", fontsize=20)
g.ax_heatmap.tick_params(axis="both", labelsize=13)

# Color y-axis (sample) labels by species
for lbl in g.ax_heatmap.get_yticklabels():
    species = lbl.get_text().rsplit("-", 1)[0]
    if species in species_colors:
        lbl.set_color(species_colors[species])
        lbl.set_fontweight("bold")

# Color x-axis (feature) labels
for lbl in g.ax_heatmap.get_xticklabels():
    lbl.set_fontsize(14)
    lbl.set_rotation(30)
    lbl.set_ha("right")

# Style the colorbar
cbar = g.cax
cbar.tick_params(labelsize=12)
cbar.set_ylabel("Feature Value", fontsize=14)

# Add species legend using scatter proxies
legend_handles = [
    plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=c, markersize=12, label=n)
    for n, c in species_colors.items()
]
g.ax_heatmap.legend(
    handles=legend_handles,
    title="Species",
    loc="upper left",
    bbox_to_anchor=(1.15, 1.0),
    fontsize=12,
    title_fontsize=13,
    framealpha=0.95,
    edgecolor="#cccccc",
    fancybox=True,
)

# Title - placed on the figure
g.figure.suptitle("dendrogram-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", y=1.02)

# Visual refinement
sns.despine(ax=g.ax_heatmap, left=False, bottom=False)

g.figure.savefig("plot.png", dpi=300, bbox_inches="tight")
