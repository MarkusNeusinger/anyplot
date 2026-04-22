""" pyplots.ai
network-directed: Directed Network Graph
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Arrow, ColumnDataSource, LabelSet, NormalHead
from bokeh.plotting import figure


# Data: Software module dependencies
np.random.seed(42)

# Define nodes (software modules)
nodes = {
    "api": {"label": "API", "group": "core"},
    "auth": {"label": "Auth", "group": "core"},
    "database": {"label": "Database", "group": "core"},
    "cache": {"label": "Cache", "group": "infra"},
    "logger": {"label": "Logger", "group": "infra"},
    "config": {"label": "Config", "group": "infra"},
    "utils": {"label": "Utils", "group": "shared"},
    "models": {"label": "Models", "group": "core"},
    "routes": {"label": "Routes", "group": "core"},
    "middleware": {"label": "Middleware", "group": "core"},
    "validators": {"label": "Validators", "group": "shared"},
    "tests": {"label": "Tests", "group": "dev"},
}

# Define directed edges (dependencies: source imports target)
edges = [
    ("api", "routes"),
    ("api", "middleware"),
    ("api", "config"),
    ("routes", "auth"),
    ("routes", "database"),
    ("routes", "models"),
    ("routes", "validators"),
    ("middleware", "auth"),
    ("middleware", "logger"),
    ("auth", "database"),
    ("auth", "cache"),
    ("auth", "config"),
    ("database", "config"),
    ("database", "logger"),
    ("cache", "config"),
    ("cache", "logger"),
    ("models", "database"),
    ("models", "validators"),
    ("validators", "utils"),
    ("tests", "api"),
    ("tests", "models"),
    ("tests", "utils"),
]

# Use circular layout for clear visualization - scaled for 4800x2700 canvas
n_nodes = len(nodes)
node_ids = list(nodes.keys())
angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)

# Position nodes in a circle - use larger scale for canvas
radius = 900
center_x, center_y = 2200, 1350

positions = {}
for i, node_id in enumerate(node_ids):
    # Offset angle to have 'api' at the top
    angle = angles[i] - np.pi / 2
    positions[node_id] = {"x": center_x + radius * np.cos(angle), "y": center_y + radius * np.sin(angle)}

# Group colors
group_colors = {
    "core": "#306998",  # Python Blue
    "infra": "#FFD43B",  # Python Yellow
    "shared": "#4ECDC4",  # Teal
    "dev": "#95A5A6",  # Gray
}

# Prepare node data
node_x = [positions[n]["x"] for n in node_ids]
node_y = [positions[n]["y"] for n in node_ids]
node_labels = [nodes[n]["label"] for n in node_ids]
node_colors = [group_colors[nodes[n]["group"]] for n in node_ids]

node_source = ColumnDataSource(data={"x": node_x, "y": node_y, "label": node_labels, "color": node_colors})

# Create figure with proper canvas size
p = figure(
    width=4800,
    height=2700,
    title="network-directed · bokeh · pyplots.ai",
    x_range=(0, 4800),
    y_range=(0, 2700),
    tools="",
    toolbar_location=None,
)

# Remove axes and grid for clean network look
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Style title
p.title.text_font_size = "36pt"
p.title.align = "center"

# Draw edges with arrows
arrow_color = "#555555"
for source_node, target_node in edges:
    sx, sy = positions[source_node]["x"], positions[source_node]["y"]
    tx, ty = positions[target_node]["x"], positions[target_node]["y"]

    # Calculate direction vector
    dx = tx - sx
    dy = ty - sy
    length = np.sqrt(dx**2 + dy**2)

    # Shorten edges to not overlap with nodes
    node_radius = 100  # Visual node radius scaled for canvas
    start_offset = node_radius / length
    end_offset = (node_radius + 35) / length  # Extra space for arrow head

    # Adjusted start and end points
    start_x = sx + dx * start_offset
    start_y = sy + dy * start_offset
    end_x = tx - dx * end_offset
    end_y = ty - dy * end_offset

    # Add arrow
    p.add_layout(
        Arrow(
            end=NormalHead(size=30, fill_color=arrow_color, line_color=arrow_color),
            x_start=start_x,
            y_start=start_y,
            x_end=end_x,
            y_end=end_y,
            line_color=arrow_color,
            line_width=4,
            line_alpha=0.7,
        )
    )

# Draw nodes - larger size for visibility
p.scatter(x="x", y="y", source=node_source, size=200, fill_color="color", line_color="#333333", line_width=4, alpha=0.9)

# Add labels on nodes
labels = LabelSet(
    x="x",
    y="y",
    text="label",
    source=node_source,
    text_font_size="22pt",
    text_color="#222222",
    text_align="center",
    text_baseline="middle",
    text_font_style="bold",
)
p.add_layout(labels)

# Add legend in upper right
legend_x = 4100
legend_y = 2450
legend_items = [
    ("Core Modules", "#306998"),
    ("Infrastructure", "#FFD43B"),
    ("Shared Utils", "#4ECDC4"),
    ("Development", "#95A5A6"),
]

# Legend background
p.rect(x=4250, y=2300, width=500, height=400, fill_color="white", fill_alpha=0.9, line_color="#999999", line_width=2)

for i, (label, color) in enumerate(legend_items):
    y_pos = legend_y - i * 80
    p.scatter(x=[legend_x], y=[y_pos], size=50, fill_color=color, line_color="#333333", line_width=2)
    p.text(
        x=[legend_x + 60], y=[y_pos], text=[label], text_font_size="22pt", text_baseline="middle", text_color="#333333"
    )

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactivity
output_file("plot.html")
save(p)
