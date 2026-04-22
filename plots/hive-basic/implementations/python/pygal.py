""" pyplots.ai
hive-basic: Basic Hive Plot
Library: pygal 3.1.0 | Python 3.13.11
Quality: 88/100 | Created: 2025-12-24
"""

import math
import re

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Set seed for reproducibility
np.random.seed(42)

# Data: Software module dependency network
# Nodes assigned to 3 axes by module type: Core (0), Utility (1), Interface (2)
nodes = [
    # Core modules (axis 0)
    {"id": 0, "label": "kernel", "axis": 0, "degree": 8},
    {"id": 1, "label": "config", "axis": 0, "degree": 6},
    {"id": 2, "label": "database", "axis": 0, "degree": 7},
    {"id": 3, "label": "auth", "axis": 0, "degree": 5},
    {"id": 4, "label": "cache", "axis": 0, "degree": 4},
    {"id": 5, "label": "logger", "axis": 0, "degree": 6},
    {"id": 6, "label": "events", "axis": 0, "degree": 5},
    # Utility modules (axis 1)
    {"id": 7, "label": "helpers", "axis": 1, "degree": 5},
    {"id": 8, "label": "validators", "axis": 1, "degree": 4},
    {"id": 9, "label": "formatters", "axis": 1, "degree": 3},
    {"id": 10, "label": "parsers", "axis": 1, "degree": 4},
    {"id": 11, "label": "converters", "axis": 1, "degree": 3},
    {"id": 12, "label": "crypto", "axis": 1, "degree": 4},
    {"id": 13, "label": "compress", "axis": 1, "degree": 2},
    # Interface modules (axis 2)
    {"id": 14, "label": "rest_api", "axis": 2, "degree": 6},
    {"id": 15, "label": "graphql", "axis": 2, "degree": 5},
    {"id": 16, "label": "websocket", "axis": 2, "degree": 4},
    {"id": 17, "label": "cli", "axis": 2, "degree": 3},
    {"id": 18, "label": "admin_ui", "axis": 2, "degree": 4},
    {"id": 19, "label": "public_ui", "axis": 2, "degree": 5},
]

# Edges: Dependencies between modules
edges = [
    # Core → Core
    (0, 1),
    (0, 2),
    (0, 3),
    (1, 4),
    (1, 5),
    (2, 4),
    (2, 5),
    (3, 6),
    # Core → Utility
    (0, 7),
    (1, 8),
    (2, 10),
    (3, 12),
    (4, 9),
    (5, 9),
    (6, 7),
    # Core → Interface
    (0, 14),
    (0, 15),
    (2, 14),
    (2, 15),
    (3, 14),
    (3, 16),
    (5, 17),
    # Utility → Utility
    (7, 8),
    (8, 10),
    (9, 11),
    (10, 11),
    (12, 13),
    # Utility → Interface
    (7, 14),
    (7, 19),
    (8, 14),
    (8, 15),
    (9, 17),
    (10, 15),
    (12, 16),
    # Interface → Interface
    (14, 18),
    (14, 19),
    (15, 19),
    (16, 18),
]

# Axis configuration (3 radial axes at 120 degrees apart)
n_axes = 3
axis_angles = [2 * math.pi * i / n_axes - math.pi / 2 for i in range(n_axes)]  # Start from top
axis_names = ["Core", "Utility", "Interface"]
axis_colors = ["#306998", "#FFD43B", "#4CAF50"]

# Calculate node positions along each axis
# Position along axis based on degree (higher degree = closer to center)
# Use larger radii to improve canvas utilization
center_x, center_y = 5.0, 5.0
inner_radius = 1.0
outer_radius = 4.2

# Sort nodes by axis and degree for positioning
axis_nodes = {i: [] for i in range(n_axes)}
for node in nodes:
    axis_nodes[node["axis"]].append(node)

# Sort each axis by degree (descending) for inner-to-outer positioning
for axis_id in axis_nodes:
    axis_nodes[axis_id].sort(key=lambda n: -n["degree"])

# Calculate positions
node_positions = {}
for axis_id in range(n_axes):
    angle = axis_angles[axis_id]
    nodes_on_axis = axis_nodes[axis_id]
    n_nodes = len(nodes_on_axis)

    for i, node in enumerate(nodes_on_axis):
        # Distribute nodes along the axis from inner to outer based on sorted order
        if n_nodes > 1:
            t = i / (n_nodes - 1)
        else:
            t = 0.5
        radius = inner_radius + t * (outer_radius - inner_radius)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        node_positions[node["id"]] = (x, y, axis_id)

# Custom style - axis lines, edges (3 groups), nodes (3 groups)
# Color order: 3 axis lines (gray), 3 edge groups (semi-transparent), 3 node groups
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=(
        "#AAAAAA",
        "#AAAAAA",
        "#AAAAAA",  # Axis lines (gray)
        "#30699866",
        "#FFD43B88",
        "#4CAF5066",  # Edges by source axis (semi-transparent)
        "#306998",
        "#FFD43B",
        "#4CAF50",  # Nodes by axis (Core, Utility, Interface)
    ),
    title_font_size=72,
    label_font_size=56,  # Increased for more prominent node labels
    major_label_font_size=48,
    legend_font_size=48,
    value_font_size=44,  # Increased for value labels on nodes
    value_label_font_size=44,  # Explicit value label size
    tooltip_font_size=32,
    stroke_width=2,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create XY chart
chart = pygal.XY(
    width=3600,
    height=3600,
    style=custom_style,
    title="hive-basic · pygal · pyplots.ai",
    show_legend=True,
    x_title="",
    y_title="",
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    stroke=True,
    dots_size=28,  # Increased for more prominent nodes
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    range=(0, 10),
    xrange=(0, 10),
    print_labels=True,  # Enable labels to show node names on the plot
    print_values=False,
)

# Draw axis lines
# Position axis labels beyond the outer nodes for visibility
label_radius = outer_radius + 0.9
for axis_id in range(n_axes):
    angle = axis_angles[axis_id]
    x1 = center_x + (inner_radius - 0.3) * math.cos(angle)
    y1 = center_y + (inner_radius - 0.3) * math.sin(angle)
    x2 = center_x + (outer_radius + 0.4) * math.cos(angle)
    y2 = center_y + (outer_radius + 0.4) * math.sin(angle)
    # Draw axis line (hidden from legend)
    chart.add(
        None,
        [(x1, y1), (x2, y2)],
        stroke=True,
        show_dots=False,
        fill=False,
        stroke_style={"width": 6, "linecap": "round"},
    )

# Store axis label positions for SVG post-processing
# (pygal's native labeling doesn't give us enough control for axis endpoint labels)
axis_label_positions = []
for axis_id in range(n_axes):
    angle = axis_angles[axis_id]
    label_x = center_x + label_radius * math.cos(angle)
    label_y = center_y + label_radius * math.sin(angle)
    axis_label_positions.append((label_x, label_y, axis_names[axis_id], axis_colors[axis_id]))

# Draw edges as curved paths between nodes, grouped by source axis for coloring
# Using quadratic Bezier curves that bend around the center
edge_points_by_axis = {0: [], 1: [], 2: []}

for src, tgt in edges:
    src_x, src_y, src_axis = node_positions[src]
    tgt_x, tgt_y, tgt_axis = node_positions[tgt]

    # Control point - pull toward center for curved edges
    # More curve for edges crossing different axes
    if src_axis == tgt_axis:
        # Same axis - slight curve
        pull = 0.7
    else:
        # Different axes - curve through center area
        pull = 0.4

    ctrl_x = center_x + pull * ((src_x + tgt_x) / 2 - center_x)
    ctrl_y = center_y + pull * ((src_y + tgt_y) / 2 - center_y)

    # Generate Bezier curve points
    n_points = 30
    for t_idx in range(n_points + 1):
        t = t_idx / n_points
        bx = (1 - t) ** 2 * src_x + 2 * (1 - t) * t * ctrl_x + t**2 * tgt_x
        by = (1 - t) ** 2 * src_y + 2 * (1 - t) * t * ctrl_y + t**2 * tgt_y
        edge_points_by_axis[src_axis].append((bx, by))
    edge_points_by_axis[src_axis].append(None)  # Break between edges

# Add edges grouped by source axis for color differentiation
for axis_id in range(n_axes):
    chart.add(
        None,
        edge_points_by_axis[axis_id],
        stroke=True,
        show_dots=False,
        fill=False,
        stroke_style={"width": 2, "linecap": "round"},
    )

# Add nodes grouped by axis for legend (simplified legend names - just axis names)
for axis_id in range(n_axes):
    nodes_on_axis = axis_nodes[axis_id]
    node_points = []
    for node in nodes_on_axis:
        x, y, _ = node_positions[node["id"]]
        # Include module name in tooltip
        node_points.append({"value": (x, y), "label": f"{node['label']} (degree: {node['degree']})"})
    # Use axis name only to avoid redundant legend entries
    chart.add(axis_names[axis_id], node_points, stroke=False)

# Render initial SVG
svg_content = chart.render().decode("utf-8")

# Post-process SVG to add axis endpoint labels directly on the plot
# Calculate SVG coordinate transformation (pygal uses viewBox scaling)
# The chart range is 0-10 for both axes, and viewBox handles the scaling
# Find the plot area in the SVG by examining the viewBox
viewbox_match = re.search(r'viewBox="([^"]+)"', svg_content)
if viewbox_match:
    vb_parts = viewbox_match.group(1).split()
    vb_width = float(vb_parts[2])
    vb_height = float(vb_parts[3])
else:
    vb_width = 3600
    vb_height = 3600

# Pygal XY chart maps data coordinates to plot area
# For range (0,10) and xrange (0,10), we need to calculate the offset and scale
# The plot area has margins for title, legend, etc.
# Approximate: plot area starts around 5% from left and 10% from top (after title)
# and ends around 95% width and 85% height (before legend)
plot_left = vb_width * 0.08
plot_right = vb_width * 0.92
plot_top = vb_height * 0.12
plot_bottom = vb_height * 0.82

plot_width = plot_right - plot_left
plot_height = plot_bottom - plot_top

# Data range is 0-10 for both axes
data_range = 10.0


def data_to_svg(dx, dy):
    """Convert data coordinates to SVG coordinates."""
    sx = plot_left + (dx / data_range) * plot_width
    # Y is inverted in SVG (0 at top)
    sy = plot_bottom - (dy / data_range) * plot_height
    return sx, sy


# Create axis label text elements
axis_label_svg = ""
for dx, dy, label, color in axis_label_positions:
    sx, sy = data_to_svg(dx, dy)
    # Adjust text anchor based on position (top label centered, bottom labels angled)
    if dy > center_y:  # Top axis (Core)
        text_anchor = "middle"
        dy_offset = -35
        dx_offset = 0
    elif dx < center_x:  # Left axis (Utility)
        text_anchor = "end"
        dy_offset = 10
        dx_offset = -25
    else:  # Right axis (Interface)
        text_anchor = "start"
        dy_offset = 10
        dx_offset = 25

    axis_label_svg += f'''
    <text x="{sx + dx_offset}" y="{sy + dy_offset}" fill="{color}"
          font-size="60" font-weight="bold" font-family="sans-serif"
          text-anchor="{text_anchor}">{label}</text>'''

# Insert axis labels before the closing </svg> tag
svg_content = svg_content.replace("</svg>", f"{axis_label_svg}\n</svg>")

# Save modified SVG
with open("plot.svg", "w") as f:
    f.write(svg_content)

# Render PNG from the modified SVG
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png")

# Save HTML for interactive version
with open("plot.html", "w") as f:
    f.write(
        """<!DOCTYPE html>
<html>
<head>
    <title>hive-basic · pygal · pyplots.ai</title>
    <style>
        body { margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 100%; margin: 0 auto; }
        object { width: 100%; height: auto; }
    </style>
</head>
<body>
    <div class="container">
        <object type="image/svg+xml" data="plot.svg">
            Hive plot not supported
        </object>
    </div>
</body>
</html>"""
    )
