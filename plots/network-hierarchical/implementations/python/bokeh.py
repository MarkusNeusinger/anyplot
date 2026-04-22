""" pyplots.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-08
"""

import os

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Legend, LegendItem
from bokeh.plotting import figure


# Data: Software project team hierarchy (24 employees, 4 levels)
np.random.seed(42)

nodes = [
    # Level 0 - CEO
    {"id": 0, "label": "CEO", "level": 0},
    # Level 1 - VPs
    {"id": 1, "label": "VP Engineering", "level": 1},
    {"id": 2, "label": "VP Product", "level": 1},
    {"id": 3, "label": "VP Operations", "level": 1},
    # Level 2 - Directors/Managers
    {"id": 4, "label": "Frontend Dir.", "level": 2},
    {"id": 5, "label": "Backend Dir.", "level": 2},
    {"id": 6, "label": "PM Lead", "level": 2},
    {"id": 7, "label": "UX Lead", "level": 2},
    {"id": 8, "label": "IT Manager", "level": 2},
    {"id": 9, "label": "HR Manager", "level": 2},
    # Level 3 - Team Members
    {"id": 10, "label": "FE Dev 1", "level": 3},
    {"id": 11, "label": "FE Dev 2", "level": 3},
    {"id": 12, "label": "BE Dev 1", "level": 3},
    {"id": 13, "label": "BE Dev 2", "level": 3},
    {"id": 14, "label": "BE Dev 3", "level": 3},
    {"id": 15, "label": "PM 1", "level": 3},
    {"id": 16, "label": "PM 2", "level": 3},
    {"id": 17, "label": "Designer 1", "level": 3},
    {"id": 18, "label": "Designer 2", "level": 3},
    {"id": 19, "label": "IT Support 1", "level": 3},
    {"id": 20, "label": "IT Support 2", "level": 3},
    {"id": 21, "label": "HR Spec 1", "level": 3},
    {"id": 22, "label": "HR Spec 2", "level": 3},
    {"id": 23, "label": "Recruiter", "level": 3},
]

edges = [
    # CEO to VPs
    (0, 1),
    (0, 2),
    (0, 3),
    # VP Engineering to Directors
    (1, 4),
    (1, 5),
    # VP Product to Leads
    (2, 6),
    (2, 7),
    # VP Operations to Managers
    (3, 8),
    (3, 9),
    # Directors to Team Members
    (4, 10),
    (4, 11),
    (5, 12),
    (5, 13),
    (5, 14),
    (6, 15),
    (6, 16),
    (7, 17),
    (7, 18),
    (8, 19),
    (8, 20),
    (9, 21),
    (9, 22),
    (9, 23),
]

# Compute hierarchical layout positions
# Group nodes by level
levels = {}
for node in nodes:
    lvl = node["level"]
    if lvl not in levels:
        levels[lvl] = []
    levels[lvl].append(node)

# Calculate positions: levels spread vertically, nodes at each level spread horizontally
positions = {}
y_spacing = 2.0  # Increased vertical spacing for better separation
for lvl in sorted(levels.keys()):
    nodes_at_level = levels[lvl]
    n = len(nodes_at_level)
    # Wider horizontal spread for lower levels
    spread = max(n * 1.4, 6)
    x_positions = np.linspace(-spread / 2, spread / 2, n)
    y_pos = -lvl * y_spacing  # Root at top, children below
    for i, node in enumerate(nodes_at_level):
        positions[node["id"]] = (x_positions[i], y_pos)

# Prepare node data
node_x = [positions[n["id"]][0] for n in nodes]
node_y = [positions[n["id"]][1] for n in nodes]
node_labels = [n["label"] for n in nodes]
node_levels = [n["level"] for n in nodes]

# Color by level - using Python Blue and Yellow as primary
level_colors = ["#306998", "#FFD43B", "#4B8BBE", "#8BC34A"]
level_names = ["CEO", "VPs", "Directors", "Team Members"]
node_colors = [level_colors[lvl] for lvl in node_levels]

# Node sizes based on level (higher in hierarchy = larger) - increased for better visibility
size_map = {0: 95, 1: 80, 2: 70, 3: 60}
node_sizes = [size_map[lvl] for lvl in node_levels]

# Prepare edge data
edge_x0 = [positions[e[0]][0] for e in edges]
edge_y0 = [positions[e[0]][1] for e in edges]
edge_x1 = [positions[e[1]][0] for e in edges]
edge_y1 = [positions[e[1]][1] for e in edges]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="network-hierarchical · bokeh · pyplots.ai",
    x_axis_label="",
    y_axis_label="",
    tools="",
    toolbar_location=None,
)

# Hide axes for cleaner network visualization
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Draw edges (lines connecting parent to child)
edge_source = ColumnDataSource(data={"x0": edge_x0, "y0": edge_y0, "x1": edge_x1, "y1": edge_y1})
p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=edge_source, line_width=4, line_color="#555555", line_alpha=0.7)

# Draw nodes by level to create legend items
renderers_by_level = {}
for lvl in range(4):
    lvl_indices = [i for i, n in enumerate(nodes) if n["level"] == lvl]
    lvl_x = [node_x[i] for i in lvl_indices]
    lvl_y = [node_y[i] for i in lvl_indices]
    lvl_labels = [node_labels[i] for i in lvl_indices]
    lvl_sizes = [node_sizes[i] for i in lvl_indices]

    source = ColumnDataSource(
        data={"x": lvl_x, "y": lvl_y, "labels": lvl_labels, "sizes": lvl_sizes, "level": [lvl] * len(lvl_indices)}
    )
    renderer = p.scatter(
        x="x",
        y="y",
        source=source,
        size="sizes",
        fill_color=level_colors[lvl],
        line_color="#333333",
        line_width=3,
        alpha=0.9,
    )
    renderers_by_level[lvl] = renderer

# Create proper legend with level colors - positioned adjacent to the graph
legend_items = [
    LegendItem(label=f"Level {lvl}: {level_names[lvl]}", renderers=[renderers_by_level[lvl]]) for lvl in range(4)
]
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="26pt",
    glyph_height=45,
    glyph_width=45,
    spacing=12,
    padding=25,
    border_line_color="#333333",
    border_line_width=2,
    background_fill_color="#f8f8f8",
    background_fill_alpha=0.8,
)
p.add_layout(legend, "right")

# Collect all node data for labels and hover
all_node_source = ColumnDataSource(data={"x": node_x, "y": node_y, "labels": node_labels, "levels": node_levels})

# Add labels to nodes with larger font for better legibility
labels = LabelSet(
    x="x",
    y="y",
    text="labels",
    source=all_node_source,
    text_font_size="28pt",
    text_color="#222222",
    text_align="center",
    y_offset=55,
)
p.add_layout(labels)

# Add hover tool for interactivity
hover = HoverTool(tooltips=[("Role", "@labels"), ("Level", "@level")], mode="mouse")
p.add_tools(hover)

# Style title
p.title.text_font_size = "36pt"
p.title.align = "center"

# Set plot range with balanced padding
x_vals = list(node_x)
y_vals = list(node_y)
x_padding = 1.0
y_padding = 1.5
p.x_range.start = min(x_vals) - x_padding
p.x_range.end = max(x_vals) + x_padding
p.y_range.start = min(y_vals) - y_padding
p.y_range.end = max(y_vals) + y_padding

# Save as PNG using absolute path
output_path = os.path.join(os.path.dirname(__file__), "plot.png")
export_png(p, filename=output_path)
