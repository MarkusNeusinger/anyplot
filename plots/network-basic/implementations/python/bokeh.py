""" pyplots.ai
network-basic: Basic Network Graph
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-23
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem
from bokeh.plotting import figure


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

# Initialize positions in a circular layout based on groups for better separation
# Position groups in a balanced 2x2 grid centered on the canvas
group_centers = {
    0: (0.35, 0.60),  # Upper-left
    1: (0.65, 0.60),  # Upper-right
    2: (0.35, 0.40),  # Lower-left
    3: (0.65, 0.40),  # Lower-right
}
positions = np.zeros((n, 2))
for i, node in enumerate(nodes):
    cx, cy = group_centers[node["group"]]
    angle = np.random.rand() * 2 * np.pi
    radius = np.random.rand() * 0.12
    positions[i] = [cx + radius * np.cos(angle), cy + radius * np.sin(angle)]

k = 0.18  # Optimal distance parameter (balanced for spread and clustering)

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

    # Attractive forces for edges (stronger for within-group)
    for src, tgt in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        force = (dist * dist / k) * (diff / dist)
        displacement[src] -= force
        displacement[tgt] += force

    # Apply displacement with cooling
    cooling = 1 - iteration / 200
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, 0.08 * cooling)

# Normalize positions to center the network on the canvas [0.15, 0.85] range
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
pos_range = pos_max - pos_min + 1e-6
# Scale to fit 70% of canvas and center
positions = (positions - pos_min) / pos_range * 0.70 + 0.15
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Calculate node degrees for sizing
degrees = {node["id"]: 0 for node in nodes}
for src, tgt in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Colors for groups (Python Blue primary, then colorblind-safe)
group_colors = ["#306998", "#FFD43B", "#4CAF50", "#FF7043"]
group_names = ["Group A", "Group B", "Group C", "Group D"]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="network-basic · bokeh · pyplots.ai",
    x_range=(-0.02, 1.02),
    y_range=(-0.02, 1.02),
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Style title and hide axes
p.title.text_font_size = "28pt"
p.title.align = "center"
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Draw edges
for src, tgt in edges:
    x0, y0 = pos[src]
    x1, y1 = pos[tgt]
    p.line([x0, x1], [y0, y1], line_width=4, line_color="#888888", line_alpha=0.5)

# Draw nodes by group (for legend)
legend_items = []
renderers_for_hover = []
for group_id, (color, name) in enumerate(zip(group_colors, group_names, strict=True)):
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
        x="x", y="y", size="size", source=source, fill_color=color, line_color="#333333", line_width=2, fill_alpha=0.9
    )
    legend_items.append(LegendItem(label=name, renderers=[renderer]))
    renderers_for_hover.append(renderer)

# Add node labels with smart positioning to avoid canvas edge issues
label_offset = 0.04  # Offset distance for labels
for node in nodes:
    x, y = pos[node["id"]]
    node_size = 45 + degrees[node["id"]] * 10

    # Smart label positioning: place labels below nodes near top, above for others
    if y > 0.75:
        # Node near top edge - place label below
        y_label = y - label_offset - node_size / 2000
        baseline = "top"
    else:
        # Default: place label above node
        y_label = y + label_offset + node_size / 2000
        baseline = "bottom"

    p.text(
        x=[x],
        y=[y_label],
        text=[node["label"]],
        text_font_size="20pt",
        text_font_style="bold",
        text_color="#222222",
        text_align="center",
        text_baseline=baseline,
    )

# Add hover tool
hover = HoverTool(tooltips=[("Name", "@label"), ("Connections", "@connections")], renderers=renderers_for_hover)
p.add_tools(hover)

# Add legend (positioned at right with large text for 4800x2700 canvas)
legend = Legend(items=legend_items, location="center", title="Communities", title_text_font_size="56pt")
legend.label_text_font_size = "48pt"
legend.background_fill_alpha = 0.95
legend.border_line_width = 4
legend.padding = 50
legend.spacing = 30
legend.glyph_height = 70
legend.glyph_width = 70
legend.margin = 40
p.add_layout(legend, "right")

# Save outputs
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
