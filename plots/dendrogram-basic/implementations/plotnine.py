"""pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 89/100 | Updated: 2026-04-05
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    guide_legend,
    guides,
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

# Branch type label for each merge: species name if pure, "Mixed" if mixed
branch_type_labels = {"Setosa": "Setosa (pure)", "Versicolor": "Versicolor (pure)", "Virginica": "Virginica (pure)"}
merge_branch_types = []
for i in range(len(linkage_matrix)):
    sp = node_species[n + i]
    if len(sp) == 1:
        merge_branch_types.append(branch_type_labels[next(iter(sp))])
    else:
        merge_branch_types.append("Mixed species")

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
        btype = merge_branch_types[merge_idx]
    else:
        btype = "Mixed species"
    segments.append({"x": xs[0], "xend": xs[1], "y": ys[0], "yend": ys[1], "branch_type": btype})
    segments.append({"x": xs[1], "xend": xs[2], "y": ys[1], "yend": ys[2], "branch_type": btype})
    segments.append({"x": xs[2], "xend": xs[3], "y": ys[2], "yend": ys[3], "branch_type": btype})

segments_df = pd.DataFrame(segments)

# Leaf labels with species-based coloring
n_leaves = len(dend["ivl"])
leaf_positions = [(i + 1) * 10 - 5 for i in range(n_leaves)]
leaf_labels = dend["ivl"]
leaf_btypes = [branch_type_labels[leaf_species[lbl]] for lbl in leaf_labels]
label_df = pd.DataFrame({"x": leaf_positions, "label": leaf_labels, "y": [0.0] * n_leaves, "branch_type": leaf_btypes})

# Ordered category for consistent legend
category_order = ["Setosa (pure)", "Versicolor (pure)", "Virginica (pure)", "Mixed species"]
color_map = {
    "Setosa (pure)": palette["Setosa"],
    "Versicolor (pure)": palette["Versicolor"],
    "Virginica (pure)": palette["Virginica"],
    "Mixed species": "#888888",
}
segments_df["branch_type"] = pd.Categorical(segments_df["branch_type"], categories=category_order, ordered=True)
label_df["branch_type"] = pd.Categorical(label_df["branch_type"], categories=category_order, ordered=True)

# Merge node points - highlight where clusters join (plotnine geom_point layer)
merge_nodes = []
for xs, ys, btype in zip(dend["icoord"], dend["dcoord"], merge_branch_types, strict=True):
    cx = (xs[1] + xs[2]) / 2
    cy = max(ys)
    merge_nodes.append({"x": cx, "y": cy, "branch_type": btype})
merge_df = pd.DataFrame(merge_nodes)
merge_df["branch_type"] = pd.Categorical(merge_df["branch_type"], categories=category_order, ordered=True)

# Key merge threshold: where Setosa separates from the rest
setosa_sep_height = linkage_matrix[-2, 2]
threshold_df = pd.DataFrame({"yintercept": [setosa_sep_height]})

# Plot
y_max = max(linkage_matrix[:, 2]) * 1.08
x_min = min(segments_df["x"].min(), segments_df["xend"].min())
x_max = max(segments_df["x"].max(), segments_df["xend"].max())
x_pad = (x_max - x_min) * 0.06

plot = (
    ggplot()
    # Dendrogram branches - thicker for HD visibility
    + geom_segment(aes(x="x", xend="xend", y="y", yend="yend", color="branch_type"), data=segments_df, size=2.2)
    # Threshold line using idiomatic geom_hline
    + geom_hline(aes(yintercept="yintercept"), data=threshold_df, linetype="dashed", color="#AAAAAA", size=0.8)
    # Threshold annotation using plotnine annotate
    + annotate(
        "text",
        x=x_max - x_pad,
        y=setosa_sep_height + 0.35,
        label="Setosa separates",
        size=13,
        color="#555555",
        fontstyle="italic",
        ha="right",
    )
    # Intermixing annotation - data storytelling for Versicolor/Virginica
    + annotate(
        "text",
        x=x_max - x_pad,
        y=linkage_matrix[-1, 2] * 0.55,
        label="Versicolor & Virginica intermixed",
        size=12,
        color="#888888",
        fontstyle="italic",
        ha="right",
    )
    # Leaf labels - larger for readability
    + geom_text(
        aes(x="x", y="y", label="label", color="branch_type"),
        data=label_df,
        angle=45,
        ha="right",
        va="top",
        size=13,
        nudge_y=-0.3,
        show_legend=False,
    )
    # Merge node markers - emphasize join points
    + geom_point(aes(x="x", y="y", color="branch_type"), data=merge_df, size=3.5, show_legend=False)
    + scale_color_manual(values=color_map, name="Branch Type")
    + guides(color=guide_legend(override_aes={"size": 4, "alpha": 1}))
    + scale_x_continuous(breaks=[], expand=(0.04, 0))
    + scale_y_continuous(breaks=np.arange(0, y_max, 2).tolist(), expand=(0.10, 0))
    + coord_cartesian(xlim=(x_min - x_pad, x_max + x_pad), ylim=(-2.5, y_max))
    + labs(
        x="",
        y="Ward Linkage Distance",
        title="Iris Species Clustering · dendrogram-basic · plotnine · pyplots.ai",
        subtitle="Hierarchical clustering of 15 iris samples using Ward's minimum variance method",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, family="sans-serif"),
        axis_title_x=element_blank(),
        axis_title_y=element_text(size=20, margin={"r": 12}),
        axis_text=element_text(size=16, color="#444444"),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        plot_title=element_text(size=24, weight="bold", margin={"b": 4}),
        plot_subtitle=element_text(size=15, color="#666666", margin={"b": 12}),
        plot_background=element_rect(fill="#FAFAFA", color="none"),
        panel_background=element_rect(fill="#FAFAFA", color="none"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_minor_y=element_blank(),
        panel_grid_major_y=element_line(alpha=0.2, size=0.5, color="#CCCCCC"),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_background=element_rect(fill="#FAFAFA", color="#DDDDDD", size=0.5),
        legend_key=element_rect(fill="none", color="none"),
        plot_margin=0.02,
    )
)

# Save with tight layout
fig = plot.draw()
fig.savefig("plot.png", dpi=300, bbox_inches="tight")
