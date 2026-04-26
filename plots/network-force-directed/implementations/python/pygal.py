""" anyplot.ai
network-force-directed: Force-Directed Graph
Library: pygal 3.1.0 | Python 3.14.4
Quality: 83/100 | Created: 2026-04-26
"""

import sys
from pathlib import Path


# Remove script directory from path to avoid name collision with pygal package
_script_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != _script_dir]

import os  # noqa: E402

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme-adaptive tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
EDGE_COLOR = "#9A988F" if THEME == "light" else "#5A5852"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442")

# Reproducibility
np.random.seed(42)

# Data: A corporate social network with 50 nodes in 3 departments
# Demonstrates force-directed layout with clear community structure
nodes = []
edges = []

community_sizes = [18, 17, 15]  # Total: 50 nodes
community_names = ["Engineering", "Marketing", "Sales"]
node_id = 0

for comm_idx, size in enumerate(community_sizes):
    for _ in range(size):
        nodes.append({"id": node_id, "community": comm_idx})
        node_id += 1

# Intra-community edges (dense connections within communities)
# Engineering: nodes 0-17
for i in range(18):
    for j in range(i + 1, 18):
        if np.random.random() < 0.3:
            edges.append((i, j))

# Marketing: nodes 18-34
for i in range(18, 35):
    for j in range(i + 1, 35):
        if np.random.random() < 0.3:
            edges.append((i, j))

# Sales: nodes 35-49
for i in range(35, 50):
    for j in range(i + 1, 50):
        if np.random.random() < 0.3:
            edges.append((i, j))

# Inter-community edges (sparse bridges between communities)
bridge_edges = [(0, 18), (5, 20), (10, 25), (18, 35), (22, 40), (30, 45), (8, 38), (15, 48)]
edges.extend(bridge_edges)

# Force-directed layout (Fruchterman-Reingold)
n = len(nodes)
positions = np.random.rand(n, 2) * 2 - 1  # Initial random positions

k = 0.95  # Optimal distance — larger to reduce dense-cluster node overlap
iterations = 320

for iteration in range(iterations):
    displacement = np.zeros((n, 2))

    # Repulsive forces between all node pairs
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            repulsive_force = (k * k / dist) * (diff / dist)
            displacement[i] += repulsive_force
            displacement[j] -= repulsive_force

    # Attractive forces along edges
    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        attractive_force = (dist * dist / k) * (diff / dist)
        displacement[src] -= attractive_force
        displacement[tgt] += attractive_force

    # Apply displacement with cooling
    temperature = 1 - iteration / iterations
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.15 * temperature)

# Normalize positions to a padded plotting range
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 10 + 1
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Node degrees (for tooltip context)
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Style — first data series is the edge "Connections" (muted), then communities use Okabe-Ito 1..3
community_colors = OKABE_ITO[: len(community_names)]
series_colors = (EDGE_COLOR,) + community_colors

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=series_colors,
    title_font_size=72,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=44,
    value_font_size=32,
    stroke_width=2,
    opacity=0.9,
    opacity_hover=1.0,
    tooltip_font_size=28,
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="network-force-directed · pygal · anyplot.ai",
    show_legend=True,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    stroke=True,
    dots_size=28,
    stroke_style={"width": 1.5, "linecap": "round"},
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=36,
    margin=80,
    range=(0, 12),
    xrange=(0, 12),
)

# Edges as a single XY series with None breaks between segments
edge_points = []
for src, tgt in edges:
    x1, y1 = pos[src]
    x2, y2 = pos[tgt]
    edge_points.append((x1, y1))
    edge_points.append((x2, y2))
    edge_points.append(None)

chart.add("Connections", edge_points, stroke=True, show_dots=False, fill=False)

# Nodes grouped by community — radius scales with node degree (visual encoding)
# pygal supports per-point SVG attribute overrides via the "node" dict
max_degree = max(degrees.values())
min_radius, max_radius = 18, 52
for comm_idx, comm_name in enumerate(community_names):
    comm_nodes = [node for node in nodes if node["community"] == comm_idx]
    node_points = []
    for node in comm_nodes:
        x, y = pos[node["id"]]
        degree = degrees[node["id"]]
        radius = min_radius + (max_radius - min_radius) * (degree / max_degree)
        label = f"Node {node['id']} | {degree} connections"
        if degree >= 7:
            label += " (Hub)"
        node_points.append({"value": (x, y), "label": label, "node": {"r": round(radius, 1)}})
    chart.add(comm_name, node_points, stroke=False)

# Save outputs (theme-aware filenames)
chart.render_to_file(f"plot-{THEME}.svg")
chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
