""" pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 85/100 | Updated: 2026-04-05
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_text,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave
from scipy.cluster.hierarchy import linkage
from sklearn.datasets import load_iris


LetsPlot.setup_html()

# Data - Iris flower measurements (15 samples, 3 species)
iris = load_iris()
np.random.seed(42)
indices = np.sort(np.concatenate([np.random.choice(np.where(iris.target == k)[0], 5, replace=False) for k in range(3)]))
features = iris.data[indices]
species_names = ["Setosa", "Versicolor", "Virginica"]
labels = [f"{species_names[iris.target[i]]}-{j + 1}" for j, i in enumerate(indices)]

# Hierarchical clustering (Ward's method)
linkage_matrix = linkage(features, method="ward")

# Build dendrogram coordinates from linkage matrix
n = len(labels)
leaf_positions = {i: float(i) for i in range(n)}
node_heights = dict.fromkeys(range(n), 0.0)
segments = []

# Color threshold — splits into 3 major clusters
max_dist = linkage_matrix[:, 2].max()
color_threshold = 0.7 * max_dist

# Track cluster identity for each node (leaf or merged)
palette = {"above": "#306998", "Setosa": "#4DAF4A", "Versicolor": "#FF7F00", "Virginica": "#984EA3"}
node_cluster = {i: labels[i].split("-")[0] for i in range(n)}

for i, (left, right, dist, _) in enumerate(linkage_matrix):
    left, right = int(left), int(right)
    new_node = n + i

    left_pos = leaf_positions[left]
    right_pos = leaf_positions[right]
    leaf_positions[new_node] = (left_pos + right_pos) / 2
    node_heights[new_node] = dist

    # Cluster label: same species if both children match, otherwise "above"
    left_cl, right_cl = node_cluster[left], node_cluster[right]
    node_cluster[new_node] = left_cl if left_cl == right_cl else "above"
    cluster_label = node_cluster[new_node] if dist < color_threshold else "above"
    color = palette[cluster_label]
    display_cluster = cluster_label if cluster_label != "above" else "Inter-cluster"

    left_height = node_heights[left]
    right_height = node_heights[right]

    # Vertical segment from left child up to merge height
    segments.append(
        {
            "x": left_pos,
            "y": left_height,
            "xend": left_pos,
            "yend": dist,
            "color": color,
            "merge_dist": round(dist, 2),
            "cluster": display_cluster,
        }
    )
    # Vertical segment from right child up to merge height
    segments.append(
        {
            "x": right_pos,
            "y": right_height,
            "xend": right_pos,
            "yend": dist,
            "color": color,
            "merge_dist": round(dist, 2),
            "cluster": display_cluster,
        }
    )
    # Horizontal segment connecting the two children
    segments.append(
        {
            "x": left_pos,
            "y": dist,
            "xend": right_pos,
            "yend": dist,
            "color": color,
            "merge_dist": round(dist, 2),
            "cluster": display_cluster,
        }
    )

segment_df = pd.DataFrame(segments)

# Leaf labels positioned just below y=0
label_df = pd.DataFrame([{"x": leaf_positions[i], "y": -0.3, "label": labels[i]} for i in range(n)])

# Plot
color_values = {v: v for v in palette.values()}

plot = (
    ggplot()
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend", color="color"),
        data=segment_df,
        size=1.8,
        tooltips=layer_tooltips().title("Merge").line("Distance|@merge_dist").line("Cluster|@cluster"),
    )
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, angle=40, hjust=1, vjust=1, size=10, color="#444444")
    + scale_color_manual(values=color_values, guide="none")
    + scale_x_continuous(expand=[0.05, 0.02])
    + scale_y_continuous(name="Ward Linkage Distance", expand=[0.14, 0.01], breaks=[0, 2, 4, 6, 8, 10, 12])
    + labs(x="", title="dendrogram-basic \u00b7 letsplot \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        axis_title_y=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_blank(),
        axis_ticks_x=element_blank(),
        axis_line_x=element_blank(),
        axis_line_y=element_line(size=0.5, color="#CCCCCC"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(size=0.5, color="#E8E8E8"),
        panel_grid_minor=element_blank(),
        plot_margin=[40, 20, 20, 20],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
