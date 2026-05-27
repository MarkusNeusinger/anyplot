""" anyplot.ai
dendrogram-radial: Radial Dendrogram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 84/100 | Created: 2026-05-14
"""

import math
import os
import sys
import time
from pathlib import Path


# Prevent the local bokeh.py from shadowing the installed bokeh package
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, LabelSet, Legend, LegendItem  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from scipy.cluster.hierarchy import leaves_list, linkage  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data — gene expression clustering scenario (40 genes, 4 clusters)
np.random.seed(42)
n_genes = 40
n_clusters = 4
cluster_size = n_genes // n_clusters

gene_names = [f"Gene-{i:02d}" for i in range(n_genes)]

cluster_centers = np.array(
    [
        [2.0, 0.5, -1.0, -0.5, 1.5, -0.8],
        [-1.5, 2.0, 0.8, -1.2, 0.3, 1.5],
        [0.5, -1.5, 2.0, 1.0, -1.0, 0.5],
        [-0.8, 0.5, -1.5, 2.0, -0.5, -1.2],
    ]
)
expression_data = np.vstack(
    [cluster_centers[c] + np.random.normal(0, 0.3, (cluster_size, 6)) for c in range(n_clusters)]
)
true_clusters = np.repeat(np.arange(n_clusters), cluster_size)

Z = linkage(expression_data, method="ward")
ordered_leaves = leaves_list(Z)

# Build radial dendrogram geometry
n_leaves = n_genes
angles = {i: 2 * math.pi * i / n_leaves for i in range(n_leaves)}
leaf_angles = {ordered_leaves[i]: angles[i] for i in range(n_leaves)}

# node_radius: leaves at 1.0, internal nodes scaled inversely by merge distance
max_dist = Z[-1, 2]
node_radius = dict.fromkeys(range(n_leaves), 1.0)
internal_id = n_leaves
for row in Z:
    node_radius[internal_id] = 1.0 - row[2] / max_dist
    internal_id += 1

# Angle for each internal node: mean of child angles
node_angle = {i: leaf_angles[i] for i in range(n_leaves)}
internal_id = n_leaves
for row in Z:
    left, right = int(row[0]), int(row[1])
    node_angle[internal_id] = (node_angle[left] + node_angle[right]) / 2
    internal_id += 1


def polar_to_xy(r, theta):
    return r * math.cos(theta), r * math.sin(theta)


def get_leaf_cluster(node_id):
    if node_id < n_leaves:
        return int(true_clusters[node_id])
    stack = [node_id]
    cluster_set = set()
    while stack:
        nid = stack.pop()
        if nid < n_leaves:
            cluster_set.add(int(true_clusters[nid]))
        else:
            row = Z[nid - n_leaves]
            stack.extend([int(row[0]), int(row[1])])
    return cluster_set.pop() if len(cluster_set) == 1 else -1


# Build branch segments
seg_xs, seg_ys, seg_colors = [], [], []
internal_id = n_leaves
for row in Z:
    left, right = int(row[0]), int(row[1])
    parent_id = internal_id

    r_parent = node_radius[parent_id]
    a_parent = node_angle[parent_id]
    a_left = node_angle[left]
    a_right = node_angle[right]

    cl = get_leaf_cluster(left)
    cr = get_leaf_cluster(right)
    cp = get_leaf_cluster(parent_id)
    color_left = IMPRINT[cl] if cl >= 0 else INK_SOFT
    color_right = IMPRINT[cr] if cr >= 0 else INK_SOFT
    color_arc = IMPRINT[cp] if cp >= 0 else INK_SOFT

    px_l, py_l = polar_to_xy(r_parent, a_left)
    cx_l, cy_l = polar_to_xy(node_radius[left], a_left)
    seg_xs.append([px_l, cx_l])
    seg_ys.append([py_l, cy_l])
    seg_colors.append(color_left)

    px_r, py_r = polar_to_xy(r_parent, a_right)
    cx_r, cy_r = polar_to_xy(node_radius[right], a_right)
    seg_xs.append([px_r, cx_r])
    seg_ys.append([py_r, cy_r])
    seg_colors.append(color_right)

    n_arc = max(3, int(abs(a_right - a_left) / (2 * math.pi) * 60))
    arc_angles = np.linspace(a_left, a_right, n_arc)
    seg_xs.append([r_parent * math.cos(a) for a in arc_angles])
    seg_ys.append([r_parent * math.sin(a) for a in arc_angles])
    seg_colors.append(color_arc)

    internal_id += 1

# Leaf label positions
label_r = 1.08
label_xs, label_ys, label_texts = [], [], []
for i, leaf_idx in enumerate(ordered_leaves):
    a = angles[i]
    lx, ly = polar_to_xy(label_r, a)
    label_xs.append(lx)
    label_ys.append(ly)
    label_texts.append(gene_names[leaf_idx])

# Cluster color dots at leaf tips
dot_xs, dot_ys, dot_colors = [], [], []
for i, leaf_idx in enumerate(ordered_leaves):
    a = angles[i]
    dx, dy = polar_to_xy(1.03, a)
    dot_xs.append(dx)
    dot_ys.append(dy)
    dot_colors.append(IMPRINT[int(true_clusters[leaf_idx])])

# Plot
W, H = 2700, 2700
p = figure(
    width=W,
    height=H,
    title="dendrogram-radial · bokeh · anyplot.ai",
    x_range=(-1.35, 1.35),
    y_range=(-1.35, 1.35),
    toolbar_location=None,
    match_aspect=True,
)

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.xaxis.visible = False
p.yaxis.visible = False

for xs, ys, color in zip(seg_xs, seg_ys, seg_colors, strict=False):
    p.line(xs, ys, line_color=color, line_width=2.5, line_alpha=0.85)

p.scatter(x=dot_xs, y=dot_ys, size=10, color=dot_colors, line_color=None, alpha=0.9)

label_source = ColumnDataSource({"x": label_xs, "y": label_ys, "text": label_texts})
labels_set = LabelSet(
    x="x",
    y="y",
    text="text",
    text_font_size="11pt",
    text_color=INK_SOFT,
    text_align="center",
    text_baseline="middle",
    source=label_source,
)
p.add_layout(labels_set)

legend_items = []
for c_idx in range(n_clusters):
    r = p.scatter([], [], size=18, color=IMPRINT[c_idx], line_color=None)
    legend_items.append(LegendItem(label=f"Cluster {c_idx + 1}", renderers=[r]))

legend = Legend(
    items=legend_items,
    location="bottom_right",
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
    label_text_color=INK_SOFT,
    label_text_font_size="14pt",
    glyph_width=20,
    glyph_height=20,
)
p.add_layout(legend)

p.title.text_font_size = "24pt"
p.title.text_color = INK
p.title.align = "center"

# Save
output_file(f"plot-{THEME}.html")
save(p)

opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)

driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
