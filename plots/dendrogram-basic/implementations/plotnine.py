""" pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 85/100 | Updated: 2026-04-05
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_text,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.datasets import load_iris


# Data - Real iris flower measurements (15 samples, 5 per species)
iris = load_iris()
np.random.seed(42)
species_names = ["Setosa", "Versicolor", "Virginica"]
species_counts = dict.fromkeys(species_names, 0)
sample_labels = []
indices = np.concatenate([np.random.choice(np.where(iris.target == i)[0], 5, replace=False) for i in range(3)])
for i in indices:
    name = species_names[iris.target[i]]
    species_counts[name] += 1
    sample_labels.append(f"{name}-{species_counts[name]}")
features = iris.data[indices]

# Hierarchical clustering with Ward's method
linkage_matrix = linkage(features, method="ward")
palette = {"Setosa": "#306998", "Versicolor": "#E8833A", "Virginica": "#55A868"}

# Extract dendrogram coordinates
dend = dendrogram(linkage_matrix, labels=sample_labels, no_plot=True)

# Track species composition of each node for branch coloring
n = len(sample_labels)
leaf_species = {lbl: lbl.rsplit("-", 1)[0] for lbl in sample_labels}
node_species = {}
for i, label in enumerate(sample_labels):
    node_species[i] = {leaf_species[label]}
for i, row in enumerate(linkage_matrix):
    left, right = int(row[0]), int(row[1])
    node_species[n + i] = node_species[left] | node_species[right]

# Color each U-shape: species color if pure, grey if mixed
merge_colors = []
for i in range(len(linkage_matrix)):
    sp = node_species[n + i]
    if len(sp) == 1:
        merge_colors.append(palette[next(iter(sp))])
    else:
        merge_colors.append("#888888")

# Map dendrogram order to linkage order via merge heights
height_to_merge = {}
for i, h in enumerate(linkage_matrix[:, 2]):
    height_to_merge.setdefault(round(h, 10), []).append(i)

# Build segment dataframe
segments = []
for xs, ys in zip(dend["icoord"], dend["dcoord"], strict=True):
    h = round(max(ys), 10)
    if h in height_to_merge and height_to_merge[h]:
        merge_idx = height_to_merge[h].pop(0)
        color = merge_colors[merge_idx]
    else:
        color = "#888888"
    segments.append({"x": xs[0], "xend": xs[1], "y": ys[0], "yend": ys[1], "color": color})
    segments.append({"x": xs[1], "xend": xs[2], "y": ys[1], "yend": ys[2], "color": color})
    segments.append({"x": xs[2], "xend": xs[3], "y": ys[2], "yend": ys[3], "color": color})

segments_df = pd.DataFrame(segments)

# Leaf labels with species-based coloring
n_leaves = len(dend["ivl"])
leaf_positions = [(i + 1) * 10 - 5 for i in range(n_leaves)]
leaf_labels = dend["ivl"]
leaf_colors = [palette[leaf_species[lbl]] for lbl in leaf_labels]
label_df = pd.DataFrame({"x": leaf_positions, "label": leaf_labels, "y": [0.0] * n_leaves, "color": leaf_colors})

# Unique colors for scale
unique_colors = sorted(set(segments_df["color"].tolist() + leaf_colors))
color_identity = {c: c for c in unique_colors}

# Plot
y_max = max(linkage_matrix[:, 2]) * 1.05
plot = (
    ggplot()
    + geom_segment(aes(x="x", xend="xend", y="y", yend="yend", color="color"), data=segments_df, size=1.6)
    + geom_text(
        aes(x="x", y="y", label="label", color="color"),
        data=label_df,
        angle=45,
        ha="right",
        va="top",
        size=9,
        nudge_y=-0.3,
    )
    + scale_color_manual(values=color_identity, guide=None)
    + scale_x_continuous(breaks=[], expand=(0.08, 0))
    + scale_y_continuous(breaks=np.arange(0, y_max, 2).tolist(), expand=(0.12, 0))
    + coord_cartesian(ylim=(-2.5, y_max))
    + labs(x="", y="Ward Linkage Distance", title="Iris Species Clustering · dendrogram-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title_x=element_blank(),
        axis_title_y=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        plot_title=element_text(size=24),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_minor_y=element_blank(),
        panel_grid_major_y=element_line(alpha=0.15, size=0.4),
    )
)

# Save with tight layout
fig = plot.draw()
fig.savefig("plot.png", dpi=300, bbox_inches="tight")
