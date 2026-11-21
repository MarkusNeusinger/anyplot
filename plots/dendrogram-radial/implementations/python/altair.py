""" anyplot.ai
dendrogram-radial: Radial Dendrogram
Library: altair 6.3.0 | Python 3.14.10
Quality: 79/100 | Updated: 2026-11-21
"""

import importlib
import os
import sys

import numpy as np
import pandas as pd
from PIL import Image
from scipy.cluster.hierarchy import leaves_list, linkage


# Import altair via importlib after removing this script's directory from sys.path,
# preventing the file named "altair.py" from shadowing the installed altair package.
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)
alt = importlib.import_module("altair")


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

TITLE = "dendrogram-radial · python · altair · anyplot.ai"

# Column names (every other column of df is one numeric expression feature)
GENE = "Gene"  # role: labels
CLUSTER = "Cluster"  # role: clusters

# Data: gene expression profiles (30 genes x 10 conditions), 5 well-separated clusters
np.random.seed(42)
cluster_ids = np.repeat(np.arange(5), 6)
cluster_centers = np.random.randn(5, 10) * 2.5
expression = np.zeros((30, 10))
for idx, c in enumerate(cluster_ids):
    expression[idx] = cluster_centers[c] + np.random.randn(10) * 0.4
df = pd.DataFrame(expression, columns=[f"Condition {j + 1}" for j in range(10)])
df.insert(0, CLUSTER, cluster_ids + 1)
df.insert(0, GENE, [f"G{idx + 1:02d}" for idx in range(30)])

# Plot: reads only df and the constants above
# Derived frame columns
PX, PY, GRP, CLR, LBL, CLS, LX, LY, ROT, RIGHT = "x", "y", "g", "clr", "label", "cluster", "lx", "ly", "angle", "right"

genes = df[GENE].tolist()
cluster_keys = sorted(df[CLUSTER].unique())
cluster_names = [f"Cluster {k}" for k in cluster_keys]
leaf_cluster = [cluster_keys.index(c) for c in df[CLUSTER]]
cluster_colors = [IMPRINT[k % len(IMPRINT)] for k in range(len(cluster_names))]
features = df.drop(columns=[GENE, CLUSTER]).apply(pd.to_numeric).to_numpy()
Z = linkage(features, method="ward")

n_leaves = len(df)
max_dist = Z[-1, 2]

# Equal angular spacing for leaves in dendrogram order; leaves sit at r = 1, the root at the center
leaf_slots = np.linspace(0, 2 * np.pi, n_leaves, endpoint=False)
node_angles = {int(leaf): ang for leaf, ang in zip(leaves_list(Z), leaf_slots, strict=False)}
node_radii = dict.fromkeys(range(n_leaves), 1.0)
subtree_clusters = {idx: {leaf_cluster[idx]} for idx in range(n_leaves)}

for i, (left, right, dist, _) in enumerate(Z):
    node_id = n_leaves + i
    left, right = int(left), int(right)
    node_radii[node_id] = 1.0 - dist / max_dist
    a1, a2 = node_angles[left], node_angles[right]
    if abs(a2 - a1) > np.pi:
        if a1 < a2:
            a1 += 2 * np.pi
        else:
            a2 += 2 * np.pi
    node_angles[node_id] = ((a1 + a2) / 2) % (2 * np.pi)
    subtree_clusters[node_id] = subtree_clusters[left] | subtree_clusters[right]

# Branch colors: the cluster color for a pure subtree, INK_SOFT for mixed merges
node_color = {
    node: cluster_colors[next(iter(cl))] if len(cl) == 1 else INK_SOFT for node, cl in subtree_clusters.items()
}

# Line segments: one arc per merge (joining the children) plus a radial line to each child
ARC_PTS = 25
rows = []
gid = 0
for i, (left, right, _dist, _) in enumerate(Z):
    left, right = int(left), int(right)
    node_id = n_leaves + i
    parent_r = node_radii[node_id]
    a1, a2 = node_angles[left], node_angles[right]
    if abs(a2 - a1) > np.pi:
        if a1 < a2:
            a1 += 2 * np.pi
        else:
            a2 += 2 * np.pi
    for theta in np.linspace(a1, a2, ARC_PTS):
        rows.append({PX: parent_r * np.cos(theta), PY: parent_r * np.sin(theta), GRP: gid, CLR: node_color[node_id]})
    gid += 1
    for child in (left, right):
        ang = node_angles[child]
        for r in (parent_r, node_radii[child]):
            rows.append({PX: r * np.cos(ang), PY: r * np.sin(ang), GRP: gid, CLR: node_color[child]})
        gid += 1
branches = pd.DataFrame(rows)

# Leaves: dots on the rim plus labels set outside, rotated along their radius
leaf_ang = np.array([node_angles[i] for i in range(n_leaves)])
LABEL_R = 1.04
deg = np.degrees(leaf_ang)
right_half = np.cos(leaf_ang) >= 0
leaves = pd.DataFrame(
    {
        PX: np.cos(leaf_ang),
        PY: np.sin(leaf_ang),
        LBL: genes,
        CLS: [cluster_names[c] for c in leaf_cluster],
        CLR: [cluster_colors[c] for c in leaf_cluster],
        LX: LABEL_R * np.cos(leaf_ang),
        LY: LABEL_R * np.sin(leaf_ang),
        ROT: np.where(right_half, -deg, 180 - deg),
        RIGHT: right_half,
    }
)

# Horizontal legend below the circle
legend_data = pd.DataFrame(
    {PX: np.linspace(-0.72, 0.72, len(cluster_names)), PY: -1.42, LBL: cluster_names, CLR: cluster_colors}
)

# Layers
all_colors = sorted(set(branches[CLR]) | set(cluster_colors))
cscale = alt.Scale(domain=all_colors, range=all_colors)
XY_DOM = [-1.5, 1.5]
x_enc = alt.X(PX, type="quantitative", scale=alt.Scale(domain=XY_DOM), axis=None)
y_enc = alt.Y(PY, type="quantitative", scale=alt.Scale(domain=XY_DOM), axis=None)
lx_enc = alt.X(LX, type="quantitative", scale=alt.Scale(domain=XY_DOM), axis=None)
ly_enc = alt.Y(LY, type="quantitative", scale=alt.Scale(domain=XY_DOM), axis=None)
color_enc = alt.Color(CLR, type="nominal", scale=cscale, legend=None)

lines_layer = (
    alt.Chart(branches)
    .mark_line(strokeWidth=1.6)
    .encode(x=x_enc, y=y_enc, detail=alt.Detail(GRP, type="nominal"), color=color_enc)
)

dots_layer = (
    alt.Chart(leaves)
    .mark_circle(size=40)
    .encode(
        x=x_enc,
        y=y_enc,
        color=color_enc,
        tooltip=[alt.Tooltip(LBL, type="nominal", title=GENE), alt.Tooltip(CLS, type="nominal", title=CLUSTER)],
    )
)


def label_layer(on_right):
    return (
        alt.Chart(leaves[leaves[RIGHT] == on_right])
        .mark_text(fontSize=9, align="left" if on_right else "right", baseline="middle")
        .encode(
            x=lx_enc,
            y=ly_enc,
            text=alt.Text(LBL, type="nominal"),
            angle=alt.Angle(ROT, type="quantitative", scale=None),
            color=alt.value(INK_SOFT),
        )
    )


legend_dots_layer = alt.Chart(legend_data).mark_circle(size=90).encode(x=x_enc, y=y_enc, color=color_enc)

legend_text_layer = (
    alt.Chart(legend_data)
    .mark_text(dy=14, fontSize=10, align="center")
    .encode(x=x_enc, y=y_enc, text=alt.Text(LBL, type="nominal"), color=alt.value(INK_SOFT))
)

chart = (
    alt.layer(lines_layer, dots_layer, label_layer(True), label_layer(False), legend_dots_layer, legend_text_layer)
    .properties(width=560, height=560, title=alt.Title(TITLE, fontSize=16), background=PAGE_BG)
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_title(color=INK)
)

# Save, then pad (never crop) to the 2400 x 2400 square target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TW, TH = 2400, 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
canvas = Image.new("RGB", (TW, TH), PAGE_BG)
canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
canvas.save(f"plot-{THEME}.png")
