"""anyplot.ai
network-directed: Directed Network Graph
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

# Ensure we import the installed pygal, not this file
import site
import sys


sys.path.insert(0, site.getsitepackages()[0])

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per node in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
EDGES = ["Source module", "Target module"]  # role: edges
SOURCE, TARGET = EDGES

# Data: software module dependencies, one row per directed edge (source imports target)
df = pd.DataFrame(
    {
        SOURCE: [
            "api",
            "api",
            "auth",
            "cache",
            "frontend",
            "frontend",
            "worker",
            "worker",
            "queue",
            "monitoring",
            "monitoring",
        ],
        TARGET: [
            "auth",
            "database",
            "cache",
            "database",
            "api",
            "auth",
            "database",
            "queue",
            "cache",
            "api",
            "database",
        ],
    }
)

# Plot: layout and geometry derived from df
nodes = sorted(set(df[SOURCE]) | set(df[TARGET]))
node_idx = {node: i for i, node in enumerate(nodes)}
n_nodes = len(nodes)
edges = list(zip(df[SOURCE], df[TARGET], strict=True))

# Force-directed layout with numpy
rng = np.random.default_rng(42)
pos = rng.normal(size=(n_nodes, 2)) * 50
for _ in range(200):
    delta = pos[:, None, :] - pos[None, :, :]
    dist = np.linalg.norm(delta, axis=2) + 0.1
    forces = (delta / dist[..., None] ** 2).sum(axis=1) * 400
    for src, dst in edges:
        i, j = node_idx[src], node_idx[dst]
        pull = (pos[j] - pos[i]) * 0.05
        forces[i] += pull
        forces[j] -= pull
    pos += np.clip(forces * 0.1, -5, 5)

# Scale into pixel-like canvas units (1 unit is about 1 px of the 3200 x 1800 canvas)
CANVAS_W, CANVAS_H = 3200, 1800
PAD_X, PAD_Y = 330, 260
span = pos.max(axis=0) - pos.min(axis=0) + 1e-8
pos = (pos - pos.min(axis=0)) / span
pos = pos * [CANVAS_W - 2 * PAD_X, CANVAS_H - 2 * PAD_Y] + [PAD_X, PAD_Y]
xy = {node: pos[node_idx[node]] for node in nodes}

NODE_RADIUS = 44
ARROW_LEN = 90
ARROW_SPREAD = 0.42  # half-angle of the arrowhead in radians

# Edge tone: muted ink blended toward the page so edges stay lighter than nodes
edge_rgb = np.array([int(INK_MUTED[k : k + 2], 16) for k in (1, 3, 5)])
bg_rgb = np.array([int(PAGE_BG[k : k + 2], 16) for k in (1, 3, 5)])
r, g, b = (0.6 * edge_rgb + 0.4 * bg_rgb).astype(int)
EDGE_COLOR = f"#{r:02X}{g:02X}{b:02X}"

style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple([EDGE_COLOR] * (2 * len(edges)) + [IMPRINT_PALETTE[i] for i in range(n_nodes)]),
    title_font_size=60,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=44,
    tooltip_font_size=36,
    stroke_width=4,
    opacity=1,
    opacity_hover=1,
)

chart = pygal.XY(
    width=CANVAS_W,
    height=CANVAS_H,
    title="network-directed · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=n_nodes,
    legend_box_size=34,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    xrange=(0, CANVAS_W),
    range=(0, CANVAS_H),
    margin=0,
    style=style,
    explicit_size=True,
)

# Edges as lines that stop at the border of the target node
for source, target in edges:
    p, q = xy[source], xy[target]
    u = (q - p) / np.linalg.norm(q - p)
    start = p + u * NODE_RADIUS
    tip = q - u * (NODE_RADIUS + 4)
    chart.add(None, [tuple(start), tuple(tip)], stroke_style={"width": 7}, show_dots=False)

# Open arrowheads (one consistent style), tip touching the target's border
for source, target in edges:
    p, q = xy[source], xy[target]
    u = (q - p) / np.linalg.norm(q - p)
    tip = q - u * (NODE_RADIUS + 4)
    wings = []
    for sign in (1, -1):
        a = sign * ARROW_SPREAD
        rot = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        wings.append(tuple(tip - (rot @ u) * ARROW_LEN))
    chart.add(None, [wings[0], tuple(tip), wings[1]], stroke_style={"width": 10, "linejoin": "round"}, show_dots=False)

# Nodes as labelled dots, labels above the node
for node in nodes:
    x, y = xy[node]
    chart.add(node, [(float(x), float(y))], stroke=False, dots_size=NODE_RADIUS)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
