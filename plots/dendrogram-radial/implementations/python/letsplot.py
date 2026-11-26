"""anyplot.ai
dendrogram-radial: Radial Dendrogram
Library: letsplot 4.11.0 | Python 3.13.15
Quality: pending | Created: 2026-08-24
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from sklearn.datasets import make_blobs


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order, one per cluster
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_CLUSTERS = 4  # the tree is cut into this many clusters, colored as sectors
STRUCTURAL = "Between clusters"  # merges that join two different clusters

# Columns: set these to your table's column names
SAMPLE = "Sample"  # role: labels

# Data: replace this block with your own table, for example
# df = pd.read_csv("expression.csv", index_col=SAMPLE); the linkage matrix and
# the cluster assignment are derived from it below the block.
# Synthetic marker-gene expression profiles for 32 tissue samples that form
# 4 latent cell-type clusters
np.random.seed(42)
expression, _ = make_blobs(n_samples=32, centers=4, n_features=6, cluster_std=1.6, random_state=42)
df = pd.DataFrame(
    expression,
    columns=[f"Gene {g}" for g in "ABCDEF"],
    index=pd.Index([f"S{i + 1:02d}" for i in range(32)], name=SAMPLE),
)

# Plot
n_leaves = len(df)
sample_labels = list(df.index)
linkage_matrix = linkage(df.to_numpy(), method="average")
cluster_ids = fcluster(linkage_matrix, t=N_CLUSTERS, criterion="maxclust")

cell_type_names = {cid: f"Cell type {chr(64 + cid)}" for cid in range(1, N_CLUSTERS + 1)}
cluster_color = {cid: IMPRINT_PALETTE[cid - 1] for cid in cell_type_names}

# Propagate cluster identity bottom-up through the linkage tree; a merge keeps
# its children's cluster label only while both sides still share one cluster,
# matching scipy's link_color_func node-id contract (node id = n_leaves + row)
node_cluster = {i: cluster_ids[i] for i in range(n_leaves)}
for i, (left, right, *_rest) in enumerate(linkage_matrix):
    left_cluster = node_cluster[int(left)]
    right_cluster = node_cluster[int(right)]
    node_cluster[n_leaves + i] = left_cluster if left_cluster == right_cluster else None

link_labels = {}
for i in range(len(linkage_matrix)):
    node_id = n_leaves + i
    cluster = node_cluster[node_id]
    link_labels[node_id] = cell_type_names[cluster] if cluster is not None else STRUCTURAL

ddata = dendrogram(
    linkage_matrix, no_plot=True, labels=sample_labels, link_color_func=lambda node_id: link_labels[node_id]
)

leaf_order = ddata["leaves"]  # original sample indices, left-to-right
icoord = ddata["icoord"]
dcoord = ddata["dcoord"]
branch_labels = ddata["color_list"]

# Column names of the derived drawing tables
X, Y, PATH, CLUSTER = "x", "y", "path_id", "cluster"
X_IN, Y_IN, X_OUT, Y_OUT = "x_in", "y_in", "x_out", "y_out"
X_LABEL, Y_LABEL, ROTATION, HJUST = "x_label", "y_label", "rotation", "hjust"
X0, X1, X_TEXT, TEXT, RING = "x0", "x1", "x_text", "text", "ring_id"

# Radial layout — root at center, leaves on the circumference, radial
# distance proportional to merge height (as in the linear dendrogram). The
# center hole is sized to hold an in-panel legend (see "Legend" below) so the
# figure never needs an external ggplot legend, which lets-plot's PNG
# exporter fails to size correctly against a fixed square canvas.
R_OUTER = 1.0
R_INNER = 0.32
max_x = n_leaves * 10
max_height = linkage_matrix[:, 2].max()


def to_angle(x):
    return (x / max_x) * 2 * np.pi


def to_radius(height):
    return R_OUTER - (height / max_height) * (R_OUTER - R_INNER)


def polar_to_xy(angle, radius):
    return radius * np.sin(angle), radius * np.cos(angle)


# Branches — each scipy "U" shape (left riser, merge bar, right riser)
# becomes a radial line, an arc sampled at the merge radius, and a radial
# line back down, all pre-projected into Cartesian x/y
branch_rows = []
for path_id, ((xl, _x1, xr, _x3), (yl, ym, _y2, yr), branch_label) in enumerate(
    zip(icoord, dcoord, branch_labels, strict=True)
):
    left_angle = to_angle(xl)
    right_angle = to_angle(xr)
    merge_radius = to_radius(ym)
    left_child_radius = to_radius(yl)
    right_child_radius = to_radius(yr)

    arc_points = max(2, round(abs(right_angle - left_angle) / (2 * np.pi) * n_leaves * 8))
    arc_angles = np.linspace(left_angle, right_angle, arc_points)

    polar_points = [(left_angle, left_child_radius), (left_angle, merge_radius)]
    polar_points += [(angle, merge_radius) for angle in arc_angles]
    polar_points.append((right_angle, right_child_radius))

    for order, (angle, radius) in enumerate(polar_points):
        px, py = polar_to_xy(angle, radius)
        branch_rows.append({PATH: path_id, "order": order, X: px, Y: py, CLUSTER: branch_label})

branches_df = pd.DataFrame(branch_rows)

# Leaves — an outer ring tick (redundant cluster encoding) plus a rotated
# label that stays upright and reads outward on both halves of the circle
leaf_rows = []
for position, sample_index in enumerate(leaf_order):
    angle = to_angle(5 + position * 10)
    cluster = cell_type_names[cluster_ids[sample_index]]

    x_in, y_in = polar_to_xy(angle, R_OUTER)
    x_out, y_out = polar_to_xy(angle, R_OUTER + 0.035)
    x_label, y_label = polar_to_xy(angle, R_OUTER + 0.075)

    angle_deg = np.degrees(angle) % 360
    if angle_deg < 180:
        rotation = angle_deg - 90
        hjust = 0
    else:
        rotation = angle_deg - 270
        hjust = 1

    leaf_rows.append(
        {
            SAMPLE: sample_labels[sample_index],
            CLUSTER: cluster,
            X_IN: x_in,
            Y_IN: y_in,
            X_OUT: x_out,
            Y_OUT: y_out,
            X_LABEL: x_label,
            Y_LABEL: y_label,
            ROTATION: rotation,
            HJUST: hjust,
        }
    )

leaves_df = pd.DataFrame(leaf_rows)

# Radial reference guide — faint dashed rings at two intermediate merge-height
# levels, so branch length has a scale anchor beyond eyeballing bare radius
RING_FRACTIONS = [1 / 3, 2 / 3]
ring_angles = np.linspace(0, 2 * np.pi, 120)
ring_rows = []
ring_label_rows = []
for ring_id, fraction in enumerate(RING_FRACTIONS):
    ring_height = fraction * max_height
    ring_radius = to_radius(ring_height)
    ring_rows += [{RING: ring_id, X: px, Y: py} for px, py in (polar_to_xy(a, ring_radius) for a in ring_angles)]
    label_x, label_y = polar_to_xy(0.02, ring_radius)
    ring_label_rows.append({X: label_x, Y: label_y, TEXT: f"h={ring_height:.1f}"})

rings_df = pd.DataFrame(ring_rows)
ring_labels_df = pd.DataFrame(ring_label_rows)

# Colors — Imprint palette for the 4 clusters, muted ink for merges that join
# two different clusters (the conventional "above cluster cut" styling)
color_values = {name: cluster_color[cid] for cid, name in cell_type_names.items()}
color_values[STRUCTURAL] = INK_MUTED

# Legend — drawn manually inside the empty center hole (color swatch + label
# per row) instead of a ggplot guide_legend(). lets-plot's PNG exporter (via
# ggsave scale=) cannot size a side/bottom legend against a fixed square
# canvas without leaving the panel letterboxed by transparent padding, so an
# in-panel legend is the reliable way to label 5 categories on this layout.
LEGEND_STEP = 0.13
legend_entries = [(f"Type {name[-1]}", name) for name in cell_type_names.values()]
legend_entries.insert(len(legend_entries) // 2, ("Mixed", STRUCTURAL))
legend_df = pd.DataFrame(
    [
        {
            Y: ((len(legend_entries) - 1) / 2 - i) * LEGEND_STEP,
            X0: -0.22,
            X1: -0.13,
            X_TEXT: -0.10,
            TEXT: text,
            CLUSTER: cluster,
        }
        for i, (text, cluster) in enumerate(legend_entries)
    ]
)

# Render
VIEW = R_OUTER * 1.55  # half-width of the square view around the tree
title = "dendrogram-radial · python · letsplot · anyplot.ai"
plot = (
    ggplot()
    + geom_path(
        aes(x=X, y=Y, group=RING),
        data=rings_df,
        color=INK_MUTED,
        size=0.4,
        alpha=0.5,
        linetype="dashed",
        show_legend=False,
    )
    + geom_text(
        aes(x=X, y=Y, label=TEXT),
        data=ring_labels_df,
        color=INK_MUTED,
        size=3.5,
        hjust=0,
        vjust=-0.3,
        show_legend=False,
    )
    + geom_path(aes(x=X, y=Y, group=PATH, color=CLUSTER), data=branches_df, size=1.1, show_legend=False)
    + geom_segment(
        aes(x=X_IN, y=Y_IN, xend=X_OUT, yend=Y_OUT, color=CLUSTER),
        data=leaves_df,
        size=3,
        show_legend=False,
        tooltips=layer_tooltips().line(f"Sample|@{SAMPLE}").line(f"Cluster|@{CLUSTER}"),
    )
    + geom_text(
        aes(x=X_LABEL, y=Y_LABEL, label=SAMPLE, angle=ROTATION, hjust=HJUST),
        data=leaves_df,
        color=INK_SOFT,
        size=8.5,
        vjust=0.5,
        show_legend=False,
    )
    + geom_segment(aes(x=X0, y=Y, xend=X1, yend=Y, color=CLUSTER), data=legend_df, size=3, show_legend=False)
    + geom_text(
        aes(x=X_TEXT, y=Y, label=TEXT), data=legend_df, color=INK_SOFT, size=6, hjust=0, vjust=0.5, show_legend=False
    )
    + scale_color_manual(values=color_values)
    + coord_fixed(ratio=1, xlim=[-VIEW, VIEW], ylim=[-VIEW, VIEW])
    + labs(title=title)
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid=element_blank(),
        panel_border=element_blank(),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        plot_title=element_text(color=INK, size=16),
    )
)
# A fixed aspect leaves the canvas edges transparent: the one-panel grid paints them
plot = gggrid([plot]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
