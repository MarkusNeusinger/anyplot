"""pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: letsplot 4.8.2 | Python 3.14.3
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
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
labels = [f"{species_names[iris.target[i]][:3]}-{j + 1}" for j, i in enumerate(indices)]

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

# Curated palette: muted, publication-quality tones
palette = {"above": "#5B7B9A", "Setosa": "#2D8E6F", "Versicolor": "#D4883B", "Virginica": "#8B6AAE"}
cluster_display = {"above": "Cross-cluster", "Setosa": "Setosa", "Versicolor": "Versicolor", "Virginica": "Virginica"}
node_cluster = {i: labels[i].split("-")[0] for i in range(n)}
# Map short prefixes to full species names
prefix_to_species = {"Set": "Setosa", "Ver": "Versicolor", "Vir": "Virginica"}
node_cluster = {i: prefix_to_species[labels[i].split("-")[0]] for i in range(n)}

for i, (left, right, dist, _) in enumerate(linkage_matrix):
    left, right = int(left), int(right)
    new_node = n + i

    left_pos = leaf_positions[left]
    right_pos = leaf_positions[right]
    leaf_positions[new_node] = (left_pos + right_pos) / 2
    node_heights[new_node] = dist

    left_cl, right_cl = node_cluster[left], node_cluster[right]
    node_cluster[new_node] = left_cl if left_cl == right_cl else "above"
    cluster_label = node_cluster[new_node] if dist < color_threshold else "above"
    color = palette[cluster_label]
    display = cluster_display[cluster_label]

    left_height = node_heights[left]
    right_height = node_heights[right]

    for seg in [
        (left_pos, left_height, left_pos, dist),
        (right_pos, right_height, right_pos, dist),
        (left_pos, dist, right_pos, dist),
    ]:
        segments.append(
            {
                "x": seg[0],
                "y": seg[1],
                "xend": seg[2],
                "yend": seg[3],
                "color": color,
                "merge_dist": round(dist, 2),
                "cluster": display,
            }
        )

segment_df = pd.DataFrame(segments)

# Leaf labels and markers
leaf_data = []
for i in range(n):
    species = prefix_to_species[labels[i].split("-")[0]]
    leaf_data.append(
        {"x": leaf_positions[i], "y": 0, "label": labels[i], "color": palette[species], "species": species}
    )
label_df = pd.DataFrame(leaf_data)

# Legend entries (manual via geom_point placed off-canvas, brought into legend via tooltips)
legend_items = pd.DataFrame(
    [
        {"x": -99, "y": -99, "xend": -98, "yend": -99, "color": palette[s], "cluster": s, "merge_dist": 0}
        for s in ["Setosa", "Versicolor", "Virginica", "above"]
    ]
)

# Plot
plot = (
    ggplot()
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend", color="color"),
        data=segment_df,
        size=2.0,
        tooltips=layer_tooltips().title("@cluster").line("Merge distance|@merge_dist").min_width(180),
    )
    + geom_point(
        aes(x="x", y="y", color="color"),
        data=label_df,
        size=5,
        shape=16,
        tooltips=layer_tooltips().title("@species").line("Sample|@label"),
    )
    + geom_text(
        aes(x="x", y="y", label="label", color="color"),
        data=label_df.assign(y=-0.35),
        angle=45,
        hjust=1,
        vjust=1,
        size=13,
        family="monospace",
    )
    + geom_hline(yintercept=color_threshold, linetype="dashed", color="#9EAAB8", size=0.8)
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=pd.DataFrame([{"x": n - 1.5, "y": color_threshold + 0.25, "label": f"threshold = {color_threshold:.1f}"}]),
        size=11,
        color="#7A8A9A",
        hjust=1,
        family="monospace",
    )
    + scale_color_identity()
    + scale_x_continuous(expand=[0.06, 0.02])
    + scale_y_continuous(name="Ward Linkage Distance", expand=[0.15, 0.01], breaks=[0, 2, 4, 6, 8, 10, 12])
    + labs(x="", title="dendrogram-basic · letsplot · pyplots.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=24, face="bold", color="#2C3E50"),
        plot_background=element_rect(fill="white", color="white"),
        axis_title_y=element_text(size=20, color="#4A5568", margin=[0, 12, 0, 0]),
        axis_text_y=element_text(size=16, color="#6B7B8D"),
        axis_text_x=element_blank(),
        axis_ticks_x=element_blank(),
        axis_ticks_y=element_line(size=0.4, color="#D0D8E0"),
        axis_line_y=element_line(size=0.6, color="#CBD5E0"),
        panel_grid_major_y=element_line(size=0.3, color="#EDF2F7"),
        plot_margin=[50, 30, 30, 20],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
