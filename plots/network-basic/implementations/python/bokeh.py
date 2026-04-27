""" anyplot.ai
network-basic: Basic Network Graph
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 82/100 | Updated: 2026-04-27
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette — first 4 positions for the 4 communities
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data: A small social network with 20 people in 4 communities
np.random.seed(42)
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

edges = [
    # Group 0 internal
    (0, 1),
    (0, 2),
    (1, 2),
    (1, 3),
    (2, 4),
    (3, 4),
    # Group 1 internal
    (5, 6),
    (5, 7),
    (6, 8),
    (7, 8),
    (7, 9),
    (8, 9),
    # Group 2 internal
    (10, 11),
    (10, 12),
    (11, 13),
    (12, 13),
    (12, 14),
    (13, 14),
    # Group 3 internal
    (15, 16),
    (15, 17),
    (16, 18),
    (17, 18),
    (17, 19),
    (18, 19),
    # Cross-group bridges
    (0, 5),
    (4, 10),
    (9, 15),
    (14, 19),
    (2, 6),
    (8, 11),
    (13, 16),
]

# Spring layout (force-directed algorithm)
n = len(nodes)
group_centers = {0: (0.35, 0.60), 1: (0.65, 0.60), 2: (0.35, 0.40), 3: (0.65, 0.40)}
positions = np.zeros((n, 2))
for i, node in enumerate(nodes):
    cx, cy = group_centers[node["group"]]
    angle = np.random.rand() * 2 * np.pi
    radius = np.random.rand() * 0.12
    positions[i] = [cx + radius * np.cos(angle), cy + radius * np.sin(angle)]

k = 0.18
for iteration in range(200):
    displacement = np.zeros((n, 2))
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            force = (k * k / dist) * (diff / dist)
            displacement[i] += force
            displacement[j] -= force
    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        force = (dist * dist / k) * (diff / dist)
        displacement[src] -= force
        displacement[tgt] += force
    cooling = 1 - iteration / 200
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.08 * cooling)

pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
pos_range = pos_max - pos_min + 1e-6
positions = (positions - pos_min) / pos_range * 0.70 + 0.15
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

group_names = ["Group A", "Group B", "Group C", "Group D"]

# Plot
p = figure(
    width=4800,
    height=2700,
    title="network-basic · bokeh · anyplot.ai",
    x_range=(-0.02, 1.02),
    y_range=(-0.02, 1.02),
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.title.text_font_size = "32pt"
p.title.align = "center"
p.title.text_color = INK
p.axis.visible = False
p.grid.visible = False

# Edges
for src, tgt in edges:
    x0, y0 = pos[src]
    x1, y1 = pos[tgt]
    p.line([x0, x1], [y0, y1], line_width=3, line_color=INK_SOFT, line_alpha=0.4)

# Nodes by group
legend_items = []
renderers_for_hover = []
for group_id, (color, name) in enumerate(zip(OKABE_ITO, group_names, strict=True)):
    group_nodes = [node for node in nodes if node["group"] == group_id]
    node_x = [pos[node["id"]][0] for node in group_nodes]
    node_y = [pos[node["id"]][1] for node in group_nodes]
    node_sizes = [45 + degrees[node["id"]] * 10 for node in group_nodes]
    node_labels = [node["label"] for node in group_nodes]
    node_degrees = [degrees[node["id"]] for node in group_nodes]

    source = ColumnDataSource(
        data={"x": node_x, "y": node_y, "size": node_sizes, "label": node_labels, "connections": node_degrees}
    )
    renderer = p.scatter(
        x="x", y="y", size="size", source=source, fill_color=color, line_color=PAGE_BG, line_width=2, fill_alpha=0.9
    )
    legend_items.append(LegendItem(label=name, renderers=[renderer]))
    renderers_for_hover.append(renderer)

# Node labels with smart edge-avoidance positioning
label_offset = 0.04
for node in nodes:
    x, y = pos[node["id"]]
    node_size = 45 + degrees[node["id"]] * 10
    if y > 0.75:
        y_label = y - label_offset - node_size / 2000
        baseline = "top"
    else:
        y_label = y + label_offset + node_size / 2000
        baseline = "bottom"
    p.text(
        x=[x],
        y=[y_label],
        text=[node["label"]],
        text_font_size="20pt",
        text_font_style="bold",
        text_color=INK,
        text_align="center",
        text_baseline=baseline,
    )

# Hover tool
hover = HoverTool(tooltips=[("Name", "@label"), ("Connections", "@connections")], renderers=renderers_for_hover)
p.add_tools(hover)

# Legend
legend = Legend(items=legend_items, location="center", title="Communities")
legend.title_text_font_size = "22pt"
legend.title_text_color = INK
legend.label_text_font_size = "18pt"
legend.label_text_color = INK_SOFT
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.95
legend.border_line_color = INK_SOFT
legend.border_line_width = 2
legend.padding = 30
legend.spacing = 20
legend.glyph_height = 50
legend.glyph_width = 50
legend.margin = 30
p.add_layout(legend, "right")

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
