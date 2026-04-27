"""anyplot.ai
network-basic: Basic Network Graph
Library: pygal 3.1.0 | Python 3.14.4
Quality: 73/100 | Updated: 2026-04-27
"""

import os

import numpy as np
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7")

# Set seed for reproducibility
np.random.seed(42)

# Data: A small social network with 20 people in 4 communities
nodes = [
    {"id": 0, "label": "Alice", "group": 0},
    {"id": 1, "label": "Bob", "group": 0},
    {"id": 2, "label": "Carol", "group": 0},
    {"id": 3, "label": "David", "group": 0},
    {"id": 4, "label": "Eve", "group": 0},
    {"id": 5, "label": "Frank", "group": 1},
    {"id": 6, "label": "Grace", "group": 1},
    {"id": 7, "label": "Henry", "group": 1},
    {"id": 8, "label": "Ivy", "group": 1},
    {"id": 9, "label": "Jack", "group": 1},
    {"id": 10, "label": "Kate", "group": 2},
    {"id": 11, "label": "Leo", "group": 2},
    {"id": 12, "label": "Mia", "group": 2},
    {"id": 13, "label": "Noah", "group": 2},
    {"id": 14, "label": "Olivia", "group": 2},
    {"id": 15, "label": "Paul", "group": 3},
    {"id": 16, "label": "Quinn", "group": 3},
    {"id": 17, "label": "Ryan", "group": 3},
    {"id": 18, "label": "Sara", "group": 3},
    {"id": 19, "label": "Tom", "group": 3},
]

# Edges: Friendship connections (within and between groups)
edges = [
    # Group 0 internal connections
    (0, 1),
    (0, 2),
    (1, 2),
    (1, 3),
    (2, 4),
    (3, 4),
    # Group 1 internal connections
    (5, 6),
    (5, 7),
    (6, 8),
    (7, 8),
    (7, 9),
    (8, 9),
    # Group 2 internal connections
    (10, 11),
    (10, 12),
    (11, 13),
    (12, 13),
    (12, 14),
    (13, 14),
    # Group 3 internal connections
    (15, 16),
    (15, 17),
    (16, 18),
    (17, 18),
    (17, 19),
    (18, 19),
    # Cross-group connections (bridges between communities)
    (0, 5),
    (4, 10),
    (9, 15),
    (14, 19),
    (2, 6),
    (8, 11),
    (13, 16),
]

# Calculate spring layout (force-directed algorithm)
n = len(nodes)

# Initialize positions clustered by group for better community structure (centered)
group_centers = {0: (-0.4, 0.4), 1: (0.4, 0.4), 2: (-0.4, -0.4), 3: (0.4, -0.4)}
positions = np.zeros((n, 2))
for i, node in enumerate(nodes):
    cx, cy = group_centers[node["group"]]
    positions[i] = [cx + np.random.rand() * 0.25 - 0.125, cy + np.random.rand() * 0.25 - 0.125]

k = 0.35  # Optimal distance parameter (slightly smaller for tighter clusters)

for iteration in range(200):
    displacement = np.zeros((n, 2))

    # Repulsive forces between all node pairs
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            force = (k * k / dist) * (diff / dist)
            displacement[i] += force
            displacement[j] -= force

    # Attractive forces for edges (stronger to keep communities tight)
    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        force = (dist * dist / k) * (diff / dist) * 1.2
        displacement[src] -= force
        displacement[tgt] += force

    # Apply displacement with cooling
    cooling = 1 - iteration / 200
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.08 * cooling)

# Normalize positions to centered range for pygal (better canvas utilization)
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6)  # Normalize to [0, 1]
positions[:, 0] = positions[:, 0] * 6 + 3  # X: [3, 9] - centered horizontally
positions[:, 1] = positions[:, 1] * 6 + 3  # Y: [3, 9] - centered vertically
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Calculate node degrees for sizing
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Custom style: theme-adaptive chrome, Okabe-Ito data colors
# Edge series comes first so its color is the neutral gray slot
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=("#888888",) + OKABE_ITO,
    title_font_size=72,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=40,
    value_font_size=32,
    stroke_width=2,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create XY chart with centered layout
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="network-basic · pygal · anyplot.ai",
    show_legend=True,
    x_title="",
    y_title="",
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    stroke=True,
    dots_size=30,
    stroke_style={"width": 2, "linecap": "round"},
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    range=(0, 12),
    xrange=(0, 12),
    print_labels=False,
    print_values=False,
)

# Add edges as a single series with lines connecting pairs
# Each edge is represented as two points connected, with None to break between edges
edge_points = []
for src, tgt in edges:
    x1, y1 = pos[src]
    x2, y2 = pos[tgt]
    edge_points.append((x1, y1))
    edge_points.append((x2, y2))
    edge_points.append(None)  # Break the line for next edge

# Add edges (using None title to exclude from legend)
chart.add(None, edge_points, stroke=True, show_dots=False, fill=False)

# Group nodes by community
group_names = ["Community A", "Community B", "Community C", "Community D"]
for group_idx in range(4):
    group_nodes = [node for node in nodes if node["group"] == group_idx]
    node_points = []
    for node in group_nodes:
        x, y = pos[node["id"]]
        degree = degrees[node["id"]]
        node_points.append({"value": (x, y), "label": f"{node['label']} ({degree} connections)"})
    chart.add(group_names[group_idx], node_points, stroke=False)

# Save themed outputs
chart.render_to_file(f"plot-{THEME}.svg")
chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
