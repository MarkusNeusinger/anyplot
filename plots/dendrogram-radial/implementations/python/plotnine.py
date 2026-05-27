""" anyplot.ai
dendrogram-radial: Radial Dendrogram
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 80/100 | Created: 2026-05-14
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
    ggplot,
    labs,
    scale_color_manual,
    theme,
)
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data: species morphological traits — 3 well-separated clades
np.random.seed(42)
n_species = 30

grp_a = np.random.randn(10, 6) + np.array([3.0, -2.0, 1.0, -1.5, 2.0, -0.5])
grp_b = np.random.randn(10, 6) + np.array([-2.0, 3.0, -1.0, 2.0, -1.5, 1.5])
grp_c = np.random.randn(10, 6) + np.array([0.0, 0.0, -3.0, 0.5, -0.5, 3.0])
features = np.vstack([grp_a, grp_b, grp_c])

# Hierarchical clustering
Z = linkage(features, method="ward")
dend = dendrogram(Z, no_plot=True)
icoord = np.array(dend["icoord"])
dcoord = np.array(dend["dcoord"])
leaves_order = dend["leaves"]

# Cluster assignment (3 clades)
cluster_assign = fcluster(Z, 3, criterion="maxclust")
clade_names = {1: "Clade I", 2: "Clade II", 3: "Clade III"}
clade_colors = {"Clade I": IMPRINT[0], "Clade II": IMPRINT[1], "Clade III": IMPRINT[2]}

# Radial coordinate transforms:
#   x position → angle (θ), evenly around the circle
#   y height   → radius (r=1 at leaf edge, r=0 at root center)
max_dist = dcoord.max()


def x_to_theta(x):
    return (x - 5.0) / (10.0 * n_species) * 2.0 * np.pi - np.pi / 2.0


def y_to_r(y):
    return 1.0 - y / max_dist


def to_xy(r, theta):
    return r * np.cos(theta), r * np.sin(theta)


# Build radial segments (vertical branches) and circular arcs (horizontal connects)
seg_rows = []
arc_rows = []
arc_id = 0

for xs, ys in zip(icoord, dcoord, strict=True):
    xl, xr = xs[0], xs[3]
    yl, yu, yr = ys[0], ys[1], ys[3]

    theta_l = x_to_theta(xl)
    theta_r = x_to_theta(xr)
    r_l, r_u, r_r = y_to_r(yl), y_to_r(yu), y_to_r(yr)

    # Left radial branch
    x1, y1 = to_xy(r_l, theta_l)
    x2, y2 = to_xy(r_u, theta_l)
    seg_rows.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

    # Right radial branch
    x1, y1 = to_xy(r_r, theta_r)
    x2, y2 = to_xy(r_u, theta_r)
    seg_rows.append({"x": x1, "y": y1, "xend": x2, "yend": y2})

    # Arc at constant r_u spanning theta_l → theta_r
    n_pts = max(12, int(abs(theta_r - theta_l) * 60))
    for t in np.linspace(theta_l, theta_r, n_pts):
        ax, ay = to_xy(r_u, t)
        arc_rows.append({"x": ax, "y": ay, "g": arc_id})
    arc_id += 1

segs_df = pd.DataFrame(seg_rows)
arcs_df = pd.DataFrame(arc_rows)

# Leaf positions and cluster labels
leaf_thetas = [x_to_theta(5.0 + 10.0 * i) for i in range(n_species)]
leaf_clades = [clade_names[cluster_assign[leaves_order[i]]] for i in range(n_species)]

leaf_df = pd.DataFrame(
    {"x": [np.cos(t) for t in leaf_thetas], "y": [np.sin(t) for t in leaf_thetas], "clade": leaf_clades}
)

# Outer metadata ring — cluster color band just beyond the leaf tips
ring_df = pd.DataFrame(
    {"x": [1.10 * np.cos(t) for t in leaf_thetas], "y": [1.10 * np.sin(t) for t in leaf_thetas], "clade": leaf_clades}
)

# Theme: square canvas, all axes hidden (circular layout needs no cartesian chrome)
anyplot_theme = theme(
    figure_size=(12, 12),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_border=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=24),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=16),
    legend_title=element_text(color=INK, size=16),
    legend_position=(0.85, 0.12),
)

# Plot
plot = (
    ggplot()
    + geom_path(data=arcs_df, mapping=aes("x", "y", group="g"), color=INK_SOFT, size=0.6)
    + geom_segment(data=segs_df, mapping=aes("x", "y", xend="xend", yend="yend"), color=INK_SOFT, size=0.6)
    + geom_point(data=leaf_df, mapping=aes("x", "y", color="clade"), size=3, show_legend=False)
    + geom_point(data=ring_df, mapping=aes("x", "y", color="clade"), size=5, shape="s")
    + scale_color_manual(name="Clade", values=clade_colors)
    + coord_equal()
    + labs(title="dendrogram-radial · plotnine · anyplot.ai")
    + anyplot_theme
)

# Save
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
