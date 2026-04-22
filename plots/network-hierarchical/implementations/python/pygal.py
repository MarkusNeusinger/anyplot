""" pyplots.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-08
"""

import pygal
from pygal.style import Style


# Define organizational hierarchy (CEO -> VPs -> Directors -> Managers)
# Structure: {node_id: (label, level, parent_id)}
hierarchy = {
    0: ("CEO", 0, None),
    1: ("VP Eng", 1, 0),
    2: ("VP Sales", 1, 0),
    3: ("VP Ops", 1, 0),
    4: ("Dir FE", 2, 1),
    5: ("Dir BE", 2, 1),
    6: ("Dir DevOps", 2, 1),
    7: ("Dir Americas", 2, 2),
    8: ("Dir EMEA", 2, 2),
    9: ("Dir Logistics", 2, 3),
    10: ("Dir HR", 2, 3),
    11: ("Mgr React", 3, 4),
    12: ("Mgr Vue", 3, 4),
    13: ("Mgr API", 3, 5),
    14: ("Mgr DB", 3, 5),
    15: ("Mgr Cloud", 3, 6),
    16: ("Mgr NA", 3, 7),
    17: ("Mgr LATAM", 3, 7),
    18: ("Mgr UK", 3, 8),
    19: ("Mgr DE", 3, 8),
    20: ("Mgr Supply", 3, 9),
    21: ("Mgr Talent", 3, 10),
}

# Group nodes by level
levels = {}
for node_id, (_label, level, _parent) in hierarchy.items():
    if level not in levels:
        levels[level] = []
    levels[level].append(node_id)

# Calculate node positions using tree layout - maximize vertical space usage
node_positions = {}
max_level = max(levels.keys())
# Use full vertical range from 10 to 90 for better canvas utilization
y_min, y_max = 10, 90
y_spacing = (y_max - y_min) / max_level

for level, nodes in levels.items():
    num_nodes = len(nodes)
    x_spacing = 90 / (num_nodes + 1)
    for i, node_id in enumerate(nodes):
        x = 5 + (i + 1) * x_spacing
        y = y_max - (level * y_spacing)  # Top to bottom layout
        node_positions[node_id] = (x, y)

# Level colors: Blue (CEO), Yellow (VPs), Teal (Directors), Coral (Managers)
level_colors = ["#306998", "#FFD43B", "#4ECDC4", "#FF6B6B"]
level_names = ["Level 0: Executive", "Level 1: VPs", "Level 2: Directors", "Level 3: Managers"]

# Create custom style with larger fonts and subtle grid
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",
    guide_stroke_color="#e0e0e0",  # Subtle light gray grid lines
    guide_stroke_dasharray="4,4",  # Dashed grid for subtlety
    colors=("#888888", "#306998", "#FFD43B", "#4ECDC4", "#FF6B6B"),  # Gray for edges
    title_font_size=72,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=40,
    value_font_size=32,
    tooltip_font_size=32,
    stroke_width=8,
    opacity=0.95,
    opacity_hover=1.0,
)

# Create XY chart with legend showing hierarchy levels
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="network-hierarchical · pygal · pyplots.ai",
    x_title="Horizontal Position (Peer Distribution)",
    y_title="Management Level (0=Top, 3=Bottom)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    show_x_guides=True,
    show_y_guides=True,
    stroke=True,
    dots_size=35,
    show_dots=True,
    range=(0, 100),
    xrange=(0, 100),
    explicit_size=True,
    truncate_legend=-1,
    margin_bottom=140,
    margin_top=100,
    x_labels=[str(i) for i in range(0, 101, 20)],
    y_labels=[str(i) for i in range(0, 101, 20)],
)

# Collect all edges
all_edges = []
for node_id, (_label, _level, parent_id) in hierarchy.items():
    if parent_id is not None:
        parent_pos = node_positions[parent_id]
        child_pos = node_positions[node_id]
        all_edges.append((parent_pos, child_pos))

# Add edges as a single series with discontinuous lines using None
edge_data = []
for start, end in all_edges:
    if edge_data:
        edge_data.append(None)
    edge_data.append(start)
    edge_data.append(end)

# Add edges with explicit stroke style for visible legend indicator
chart.add("Reporting Lines", edge_data, show_dots=False, stroke=True, stroke_style={"width": 6, "dasharray": "none"})

# Group nodes by level and add as separate series for proper legend
# Include node labels in the data for visibility via tooltips
for level_idx in range(max_level + 1):
    level_nodes = levels[level_idx]
    level_data = []
    for node_id in level_nodes:
        pos = node_positions[node_id]
        node_label = hierarchy[node_id][0]
        # Add position with tooltip label for interactivity
        level_data.append({"value": pos, "label": node_label})
    chart.add(level_names[level_idx], level_data, stroke=False, color=level_colors[level_idx])

# Render to PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
