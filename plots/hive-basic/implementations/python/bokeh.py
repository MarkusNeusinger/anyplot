""" pyplots.ai
hive-basic: Basic Hive Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 85/100 | Created: 2025-12-24
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data: Software module dependency network
# Nodes assigned to 3 axes by module type: Core, Utility, Interface
np.random.seed(42)

nodes = {
    # Core modules (axis 0)
    "core_main": {"axis": 0, "degree": 8},
    "core_data": {"axis": 0, "degree": 6},
    "core_config": {"axis": 0, "degree": 5},
    "core_init": {"axis": 0, "degree": 7},
    "core_base": {"axis": 0, "degree": 4},
    # Utility modules (axis 1)
    "util_io": {"axis": 1, "degree": 5},
    "util_parse": {"axis": 1, "degree": 4},
    "util_cache": {"axis": 1, "degree": 3},
    "util_log": {"axis": 1, "degree": 6},
    "util_helper": {"axis": 1, "degree": 2},
    "util_validate": {"axis": 1, "degree": 4},
    # Interface modules (axis 2)
    "api_rest": {"axis": 2, "degree": 7},
    "api_graphql": {"axis": 2, "degree": 5},
    "api_cli": {"axis": 2, "degree": 4},
    "api_web": {"axis": 2, "degree": 6},
}

edges = [
    # Core to Utility connections
    ("core_main", "util_io"),
    ("core_main", "util_log"),
    ("core_main", "util_cache"),
    ("core_data", "util_parse"),
    ("core_data", "util_io"),
    ("core_data", "util_validate"),
    ("core_config", "util_io"),
    ("core_config", "util_parse"),
    ("core_init", "util_log"),
    ("core_init", "util_helper"),
    ("core_base", "util_validate"),
    # Utility to Interface connections
    ("util_io", "api_rest"),
    ("util_io", "api_web"),
    ("util_parse", "api_graphql"),
    ("util_parse", "api_cli"),
    ("util_cache", "api_rest"),
    ("util_cache", "api_graphql"),
    ("util_log", "api_rest"),
    ("util_log", "api_cli"),
    ("util_log", "api_web"),
    ("util_validate", "api_rest"),
    ("util_validate", "api_graphql"),
    # Core to Interface connections (cross-axis)
    ("core_main", "api_rest"),
    ("core_main", "api_web"),
    ("core_data", "api_graphql"),
    ("core_init", "api_cli"),
]

# Hive plot parameters
n_axes = 3
# Rotate axes to point outward from center: up-right, up-left, down
axis_angles = [np.pi / 6, 5 * np.pi / 6, 3 * np.pi / 2]  # 120° apart, starting from 30°
inner_radius = 450
outer_radius = 1400
axis_colors = ["#306998", "#FFD43B", "#4CAF50"]  # Python Blue, Python Yellow, Green
axis_labels = ["Core", "Utility", "Interface"]

# Calculate node positions on axes
node_positions = {}
for axis_id in range(n_axes):
    axis_nodes = [(name, data) for name, data in nodes.items() if data["axis"] == axis_id]
    # Sort by degree for positioning along axis
    axis_nodes.sort(key=lambda x: x[1]["degree"])
    n_nodes = len(axis_nodes)
    for i, (name, data) in enumerate(axis_nodes):
        # Position along axis based on index (evenly spaced)
        t = (i + 0.5) / n_nodes
        radius = inner_radius + t * (outer_radius - inner_radius)
        angle = axis_angles[axis_id]
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        node_positions[name] = {"x": x, "y": y, "axis": axis_id, "degree": data["degree"]}

# Create figure - tighter ranges for better canvas utilization
p = figure(
    width=3600,
    height=3600,
    title="hive-basic · bokeh · pyplots.ai",
    x_range=(-1750, 1750),
    y_range=(-1700, 1800),
    tools="",
    toolbar_location=None,
)

# Remove axes and grid for circular plot
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Styling - larger text for better readability
p.title.text_font_size = "48pt"
p.title.align = "center"
p.background_fill_color = "#FAFAFA"

# Draw radial axes - thicker lines for better visibility
for i, angle in enumerate(axis_angles):
    x_start = inner_radius * np.cos(angle)
    y_start = inner_radius * np.sin(angle)
    x_end = outer_radius * np.cos(angle)
    y_end = outer_radius * np.sin(angle)
    p.line([x_start, x_end], [y_start, y_end], line_width=10, line_color="#666666", line_alpha=0.7)
    # Axis label - larger text, positioned further out
    label_radius = outer_radius + 250
    label_x = label_radius * np.cos(angle)
    label_y = label_radius * np.sin(angle)
    label = Label(
        x=label_x,
        y=label_y,
        text=axis_labels[i],
        text_font_size="42pt",
        text_align="center",
        text_baseline="middle",
        text_color=axis_colors[i],
        text_font_style="bold",
    )
    p.add_layout(label)

# Draw edges as bezier curves
for source, target in edges:
    src_pos = node_positions[source]
    tgt_pos = node_positions[target]

    # Control point at center for smooth curves
    # Offset slightly based on edge position for visual separation
    ctrl_x = (src_pos["x"] + tgt_pos["x"]) * 0.2
    ctrl_y = (src_pos["y"] + tgt_pos["y"]) * 0.2

    # Create bezier curve points
    t_vals = np.linspace(0, 1, 30)
    curve_x = (1 - t_vals) ** 2 * src_pos["x"] + 2 * (1 - t_vals) * t_vals * ctrl_x + t_vals**2 * tgt_pos["x"]
    curve_y = (1 - t_vals) ** 2 * src_pos["y"] + 2 * (1 - t_vals) * t_vals * ctrl_y + t_vals**2 * tgt_pos["y"]

    # Color based on source axis
    edge_color = axis_colors[src_pos["axis"]]
    p.line(curve_x.tolist(), curve_y.tolist(), line_width=3, line_color=edge_color, line_alpha=0.5)

# Draw nodes - larger sizes for better visibility on high-res canvas
for axis_id in range(n_axes):
    axis_node_data = [(name, data) for name, data in node_positions.items() if data["axis"] == axis_id]
    x_coords = [d["x"] for _, d in axis_node_data]
    y_coords = [d["y"] for _, d in axis_node_data]
    names = [name for name, _ in axis_node_data]
    sizes = [40 + d["degree"] * 6 for _, d in axis_node_data]  # Larger nodes

    source = ColumnDataSource(data={"x": x_coords, "y": y_coords, "size": sizes, "name": names})

    p.scatter(
        x="x",
        y="y",
        size="size",
        source=source,
        fill_color=axis_colors[axis_id],
        line_color="white",
        line_width=4,
        alpha=0.9,
    )

# Add node labels for identification - positioned perpendicular to axis for visibility
for name, data in node_positions.items():
    angle = axis_angles[data["axis"]]
    # Offset perpendicular to axis (not along it) to avoid overlapping axis line
    perp_angle = angle + np.pi / 2  # 90 degrees perpendicular
    label_offset = 100
    label_x = data["x"] + label_offset * np.cos(perp_angle)
    label_y = data["y"] + label_offset * np.sin(perp_angle)

    # Shorter display name (remove prefix)
    short_name = name.split("_")[1] if "_" in name else name

    node_label = Label(
        x=label_x,
        y=label_y,
        text=short_name,
        text_font_size="26pt",
        text_align="center",
        text_baseline="middle",
        text_color="#222222",
        text_font_style="bold",
    )
    p.add_layout(node_label)

# Add legend for node size - repositioned for visibility
legend_x = 1150
legend_y = -1300
legend_title = Label(
    x=legend_x,
    y=legend_y,
    text="Node Size = Degree",
    text_font_size="32pt",
    text_align="left",
    text_baseline="middle",
    text_color="#333333",
    text_font_style="bold",
)
p.add_layout(legend_title)

# Add legend items showing size scale
legend_sizes = [2, 5, 8]
legend_labels = ["Low (2)", "Medium (5)", "High (8)"]
for i, (deg, label_text) in enumerate(zip(legend_sizes, legend_labels, strict=True)):
    node_size = 40 + deg * 6  # Match updated node size formula
    item_y = legend_y - 100 - i * 90
    # Draw sample node
    p.scatter(
        [legend_x + 40], [item_y], size=node_size, fill_color="#666666", line_color="white", line_width=3, alpha=0.9
    )
    # Draw label
    size_label = Label(
        x=legend_x + 120,
        y=item_y,
        text=label_text,
        text_font_size="26pt",
        text_align="left",
        text_baseline="middle",
        text_color="#555555",
    )
    p.add_layout(size_label)

# Save outputs
export_png(p, filename="plot.png")

# Also save HTML for interactivity
save(p, filename="plot.html", resources=CDN, title="hive-basic · bokeh · pyplots.ai")
