"""anyplot.ai
dendrogram-basic: Basic Dendrogram
Library: letsplot | Python
"""

import os

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
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)
from lets_plot.export import ggsave
from scipy.cluster.hierarchy import linkage
from sklearn.datasets import load_iris


LetsPlot.setup_html()

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — positions 1-4 in canonical order
CLUSTER_COLORS = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
CLUSTER_BREAKS = ["Setosa", "Versicolor", "Virginica", "Cross-cluster"]

# Data — Iris flower measurements (15 samples, 3 species)
iris = load_iris()
np.random.seed(42)
indices = np.sort(np.concatenate([np.random.choice(np.where(iris.target == k)[0], 5, replace=False) for k in range(3)]))
features = iris.data[indices]
species_names = ["Setosa", "Versicolor", "Virginica"]
labels = [f"{species_names[iris.target[i]][:3]}-{j + 1}" for j, i in enumerate(indices)]

# Hierarchical clustering (Ward's method)
linkage_matrix = linkage(features, method="ward")

# Build dendrogram segment coordinates from linkage matrix
n = len(labels)
leaf_positions = {i: float(i) for i in range(n)}
node_heights = dict.fromkeys(range(n), 0.0)
segments = []

# Color threshold at 70% of max distance — splits into 3 major species clusters
max_dist = linkage_matrix[:, 2].max()
color_threshold = 0.7 * max_dist

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
    node_cluster[new_node] = left_cl if left_cl == right_cl else "Cross-cluster"
    cluster_label = node_cluster[new_node] if dist < color_threshold else "Cross-cluster"

    lh, rh = node_heights[left], node_heights[right]
    for seg in [(left_pos, lh, left_pos, dist), (right_pos, rh, right_pos, dist), (left_pos, dist, right_pos, dist)]:
        segments.append(
            {
                "x": seg[0],
                "y": seg[1],
                "xend": seg[2],
                "yend": seg[3],
                "cluster": cluster_label,
                "merge_dist": round(dist, 2),
            }
        )

segment_df = pd.DataFrame(segments)

leaf_data = [
    {"x": leaf_positions[i], "y": 0, "label": labels[i], "cluster": prefix_to_species[labels[i].split("-")[0]]}
    for i in range(n)
]
label_df = pd.DataFrame(leaf_data)

plot = (
    ggplot()
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend", color="cluster"),
        data=segment_df,
        size=1.5,
        tooltips=layer_tooltips().title("@cluster").line("Merge distance|@merge_dist").min_width(180),
    )
    + geom_point(
        aes(x="x", y="y", color="cluster"),
        data=label_df,
        size=2.5,
        shape=16,
        show_legend=False,
        tooltips=layer_tooltips().title("@cluster").line("Sample|@label"),
    )
    + geom_text(
        aes(x="x", y="y", label="label", color="cluster"),
        data=label_df.assign(y=-max_dist * 0.05),
        angle=45,
        hjust=1,
        vjust=1,
        size=4,
        family="monospace",
        show_legend=False,
    )
    + geom_hline(yintercept=color_threshold, linetype="dashed", color=INK_MUTED, size=0.8)
    + geom_text(
        aes(x="x", y="y", label="label"),
        data=pd.DataFrame(
            [{"x": n - 1.8, "y": color_threshold + max_dist * 0.03, "label": f"threshold = {color_threshold:.1f}"}]
        ),
        size=3.5,
        color=INK_MUTED,
        hjust=1,
        family="monospace",
    )
    + scale_color_manual(values=CLUSTER_COLORS, breaks=CLUSTER_BREAKS, name="Cluster")
    + scale_x_continuous(expand=[0.06, 0.02])
    + scale_y_continuous(
        name="Ward Linkage Distance",
        limits=[-max_dist * 0.14, max_dist * 1.07],
        expand=[0, 0],
        breaks=[0, 2, 4, 6, 8, 10, 12],
    )
    + labs(x="", title="dendrogram-basic · letsplot · anyplot.ai")
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=16, face="bold", color=INK),
        axis_title_y=element_text(size=12, color=INK_SOFT, margin=[0, 8, 0, 0]),
        axis_text_y=element_text(size=10, color=INK_SOFT),
        axis_text_x=element_blank(),
        axis_ticks_x=element_blank(),
        axis_ticks_y=element_line(size=0.4, color=INK_SOFT),
        axis_line_y=element_line(size=0.6, color=INK_SOFT),
        panel_grid_major_y=element_line(size=0.3, color=INK_MUTED),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=10, color=INK),
        plot_margin=[25, 15, 20, 10],
    )
    + ggsize(800, 450)
)

ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
