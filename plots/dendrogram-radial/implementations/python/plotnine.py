""" anyplot.ai
dendrogram-radial: Radial Dendrogram
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
"""

import os
import sys


# Prevent this script (plotnine.py) from shadowing the plotnine library
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_equal,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per clade in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_CLADES = 3  # the tree is cut into this many clusters when no cluster column is given

# Columns: set these to your table's names
SPECIES = "Species"  # role: labels

# Data: replace this block with your own table, for example df = pd.read_csv("traits.csv")
rng = np.random.default_rng(42)
centers = np.array(
    [[3.0, -2.0, 1.0, -1.5, 2.0, -0.5], [-2.0, 3.0, -1.0, 2.0, -1.5, 1.5], [0.0, 0.0, -3.0, 0.5, -0.5, 3.0]]
)
genera = ["Corvus", "Pica", "Garrulus"]
epithets = ["alba", "major", "minor", "rufa", "nigra", "pallida", "borealis", "austral", "montana", "riparia"]
df = pd.DataFrame(
    np.vstack([rng.standard_normal((10, 6)) + c for c in centers]),
    index=pd.Index([f"{g} {e}" for g in genera for e in epithets], name=SPECIES),
    columns=[f"Trait {i}" for i in range(1, 7)],
)

# Plot: reads only df and the constants above
Z = linkage(df.to_numpy(), method="ward")
n_leaves = len(df)
cut = (Z[-N_CLADES, 2] + Z[-N_CLADES + 1, 2]) / 2  # between the last two merges that separate the clades
dend = dendrogram(Z, no_plot=True, color_threshold=cut, above_threshold_color="k")
icoord = np.array(dend["icoord"])
dcoord = np.array(dend["dcoord"])
leaves_order = dend["leaves"]
cluster_assign = fcluster(Z, cut, criterion="distance")

# Clades are numbered in leaf order, so the first clade around the circle gets the first palette color
clade_ids = list(dict.fromkeys(cluster_assign[leaves_order]))
clade_names = {cid: f"Clade {i + 1}" for i, cid in enumerate(clade_ids)}
clade_colors = {clade_names[cid]: IMPRINT_PALETTE[i] for i, cid in enumerate(clade_ids)}
leaf_clades = [clade_names[cluster_assign[k]] for k in leaves_order]
color_to_clade = dict(zip(dend["leaves_color_list"], leaf_clades, strict=True))

# Radial transform: dendrogram x (leaf slots of width 10) -> angle, merge distance -> radius (root at 0, leaves at 1)
max_dist = dcoord.max()
theta = lambda x: (x - 5.0) / (10.0 * n_leaves) * 2.0 * np.pi - np.pi / 2.0  # noqa: E731
radius = lambda y: 1.0 - y / max_dist  # noqa: E731

seg_rows, arc_rows = [], []
for i, (xs, ys, col) in enumerate(zip(icoord, dcoord, dend["color_list"], strict=True)):
    clade = color_to_clade.get(col, "Between clades")
    th_l, th_r = theta(xs[0]), theta(xs[3])
    r_l, r_u, r_r = radius(ys[0]), radius(ys[1]), radius(ys[3])
    seg_rows.append((r_l * np.cos(th_l), r_l * np.sin(th_l), r_u * np.cos(th_l), r_u * np.sin(th_l), clade))
    seg_rows.append((r_r * np.cos(th_r), r_r * np.sin(th_r), r_u * np.cos(th_r), r_u * np.sin(th_r), clade))
    for t in np.linspace(th_l, th_r, max(12, int(abs(th_r - th_l) * 60))):
        arc_rows.append((r_u * np.cos(t), r_u * np.sin(t), i, clade))

segs = pd.DataFrame(seg_rows, columns=["x", "y", "xend", "yend", "clade"])
arcs = pd.DataFrame(arc_rows, columns=["x", "y", "g", "clade"])
between_segs, clade_segs = segs[segs.clade == "Between clades"], segs[segs.clade != "Between clades"]
between_arcs, clade_arcs = arcs[arcs.clade == "Between clades"], arcs[arcs.clade != "Between clades"]

# Leaves: colored ring just outside the tips, species labels fanned along the radius
leaf_theta = theta(5.0 + 10.0 * np.arange(n_leaves))
deg = np.degrees(leaf_theta)
left = np.cos(leaf_theta) < 0
# Rotated text is centered on its anchor, so push each label out by half its length
labels = df.index.to_numpy()[leaves_order]
text_r = 1.12 + 0.0185 * np.array([len(s) for s in labels]) + 0.01
leaves = pd.DataFrame(
    {
        "x": np.cos(leaf_theta),
        "y": np.sin(leaf_theta),
        "rx": 1.07 * np.cos(leaf_theta),
        "ry": 1.07 * np.sin(leaf_theta),
        "tx": text_r * np.cos(leaf_theta),
        "ty": text_r * np.sin(leaf_theta),
        "angle": np.where(left, deg + 180.0, deg),
        "label": labels,
        "clade": leaf_clades,
        "left": left,
    }
)

reach = 1.7
anyplot_theme = theme(
    figure_size=(6, 6),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_blank(),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=15),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=10),
    legend_position=(0.02, 0.02),
)

plot = (
    ggplot()
    + geom_path(data=between_arcs, mapping=aes("x", "y", group="g"), color=INK_SOFT, size=0.8)
    + geom_segment(data=between_segs, mapping=aes("x", "y", xend="xend", yend="yend"), color=INK_SOFT, size=0.8)
    + geom_path(data=clade_arcs, mapping=aes("x", "y", group="g", color="clade"), size=0.8, show_legend=False)
    + geom_segment(
        data=clade_segs, mapping=aes("x", "y", xend="xend", yend="yend", color="clade"), size=0.8, show_legend=False
    )
    + geom_point(data=leaves, mapping=aes("x", "y", color="clade"), size=1.5, show_legend=False)
    + geom_point(data=leaves, mapping=aes("rx", "ry", color="clade"), size=3, shape="s")
    + geom_text(
        data=leaves[~leaves["left"]],
        mapping=aes("tx", "ty", label="label", angle="angle"),
        color=INK,
        size=7,
        ha="center",
        va="center",
    )
    + geom_text(
        data=leaves[leaves["left"]],
        mapping=aes("tx", "ty", label="label", angle="angle"),
        color=INK,
        size=7,
        ha="center",
        va="center",
    )
    + scale_color_manual(name="Clade", values=clade_colors)
    + scale_x_continuous(limits=(-reach, reach))
    + scale_y_continuous(limits=(-reach, reach))
    + coord_equal()
    + labs(title="dendrogram-radial · python · plotnine · anyplot.ai")
    + anyplot_theme
)

plot.save(f"plot-{THEME}.png", dpi=400, verbose=False)
