""" pyplots.ai
hive-basic: Basic Hive Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection


# Set random seed for reproducibility
np.random.seed(42)

# Create software module dependency network data
# Nodes with module type (axis assignment) and degree-like importance
nodes = [
    # Core modules (axis 0)
    {"id": "core_engine", "axis": 0, "order": 0.9, "label": "Engine"},
    {"id": "core_config", "axis": 0, "order": 0.7, "label": "Config"},
    {"id": "core_logger", "axis": 0, "order": 0.5, "label": "Logger"},
    {"id": "core_cache", "axis": 0, "order": 0.3, "label": "Cache"},
    # Utility modules (axis 1)
    {"id": "util_parser", "axis": 1, "order": 0.85, "label": "Parser"},
    {"id": "util_validator", "axis": 1, "order": 0.65, "label": "Validator"},
    {"id": "util_formatter", "axis": 1, "order": 0.45, "label": "Formatter"},
    {"id": "util_converter", "axis": 1, "order": 0.25, "label": "Converter"},
    {"id": "util_helper", "axis": 1, "order": 0.15, "label": "Helper"},
    # Interface modules (axis 2)
    {"id": "iface_api", "axis": 2, "order": 0.95, "label": "API"},
    {"id": "iface_web", "axis": 2, "order": 0.75, "label": "Web"},
    {"id": "iface_cli", "axis": 2, "order": 0.55, "label": "CLI"},
    {"id": "iface_sdk", "axis": 2, "order": 0.35, "label": "SDK"},
]

# Create node lookup
node_lookup = {n["id"]: n for n in nodes}

# Dependencies between modules
edges = [
    # Core to Utility connections
    ("core_engine", "util_parser"),
    ("core_engine", "util_validator"),
    ("core_config", "util_parser"),
    ("core_logger", "util_formatter"),
    ("core_cache", "util_helper"),
    # Utility to Interface connections
    ("util_parser", "iface_api"),
    ("util_validator", "iface_api"),
    ("util_formatter", "iface_web"),
    ("util_converter", "iface_sdk"),
    ("util_helper", "iface_cli"),
    # Core to Interface connections
    ("core_engine", "iface_api"),
    ("core_config", "iface_cli"),
    ("core_logger", "iface_web"),
    # Intra-axis connections (within same group)
    ("core_engine", "core_config"),
    ("core_engine", "core_logger"),
    ("util_parser", "util_validator"),
    ("iface_api", "iface_sdk"),
]

# Hive plot configuration
n_axes = 3
axis_angles = [np.pi / 2 + i * 2 * np.pi / n_axes for i in range(n_axes)]  # 120 degrees apart
axis_labels = ["Core", "Utility", "Interface"]
axis_colors = ["#306998", "#FFD43B", "#4ECDC4"]  # Python blue, Python yellow, teal

# Radii for the axes
inner_radius = 0.15
outer_radius = 0.85


# Function to convert node to cartesian coordinates
def node_to_cartesian(node):
    angle = axis_angles[node["axis"]]
    # Position along axis based on order (importance/degree)
    r = inner_radius + node["order"] * (outer_radius - inner_radius)
    x = r * np.cos(angle)
    y = r * np.sin(angle)
    return x, y


# Create figure with square aspect for radial symmetry
fig, ax = plt.subplots(figsize=(12, 12))

# Draw axes as thick lines
for i in range(n_axes):
    angle = axis_angles[i]
    x_inner = inner_radius * np.cos(angle)
    y_inner = inner_radius * np.sin(angle)
    x_outer = outer_radius * np.cos(angle)
    y_outer = outer_radius * np.sin(angle)

    # Draw axis line
    ax.plot([x_inner, x_outer], [y_inner, y_outer], color=axis_colors[i], linewidth=6, solid_capstyle="round", zorder=1)

    # Add axis label at the end
    label_r = outer_radius + 0.08
    label_x = label_r * np.cos(angle)
    label_y = label_r * np.sin(angle)
    ax.text(
        label_x, label_y, axis_labels[i], fontsize=22, fontweight="bold", ha="center", va="center", color=axis_colors[i]
    )

# Draw edges as curved bezier curves
edge_lines = []
edge_colors = []

for source_id, target_id in edges:
    source = node_lookup[source_id]
    target = node_lookup[target_id]

    x1, y1 = node_to_cartesian(source)
    x2, y2 = node_to_cartesian(target)

    # Create bezier curve through center for smooth connection
    # Control point near center
    ctrl_x = 0
    ctrl_y = 0

    # Generate curve points using quadratic bezier
    t = np.linspace(0, 1, 50)
    curve_x = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * ctrl_x + t**2 * x2
    curve_y = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * ctrl_y + t**2 * y2

    points = np.column_stack([curve_x, curve_y])
    segments = np.array([points[:-1], points[1:]]).transpose(1, 0, 2)
    edge_lines.extend(segments)

    # Color based on source axis
    edge_colors.extend([axis_colors[source["axis"]]] * len(segments))

# Draw all edges with LineCollection for efficiency
lc = LineCollection(edge_lines, colors=edge_colors, linewidths=2.5, alpha=0.4, zorder=2)
ax.add_collection(lc)

# Draw nodes
for node in nodes:
    x, y = node_to_cartesian(node)
    color = axis_colors[node["axis"]]

    # Draw node marker
    ax.scatter(x, y, s=400, c=color, edgecolors="white", linewidths=3, zorder=3)

    # Add node label with offset based on axis position
    offset_dist = 0.08

    # Adjust horizontal alignment based on axis position
    if node["axis"] == 0:  # Core (top)
        ha = "left"
        label_x = x + offset_dist
        label_y = y
    elif node["axis"] == 1:  # Utility (bottom-left)
        ha = "right"
        label_x = x - offset_dist * 0.5
        label_y = y + offset_dist * 0.3
    else:  # Interface (bottom-right)
        ha = "left"
        label_x = x + offset_dist * 0.5
        label_y = y + offset_dist * 0.3

    ax.text(label_x, label_y, node["label"], fontsize=16, ha=ha, va="center", color="#333333")

# Draw center point
ax.scatter(0, 0, s=200, c="white", edgecolors="#666666", linewidths=3, zorder=4)

# Styling
ax.set_xlim(-1.1, 1.1)
ax.set_ylim(-1.1, 1.1)
ax.set_aspect("equal")
ax.axis("off")

# Title
ax.set_title(
    "Software Module Dependencies\nhive-basic \u00b7 matplotlib \u00b7 pyplots.ai",
    fontsize=26,
    fontweight="bold",
    pad=20,
)

# Add legend for module types
legend_elements = [
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        markerfacecolor=axis_colors[i],
        markersize=18,
        markeredgecolor="white",
        markeredgewidth=2,
        label=axis_labels[i],
    )
    for i in range(n_axes)
]
ax.legend(handles=legend_elements, loc="lower center", fontsize=18, frameon=True, ncol=3, bbox_to_anchor=(0.5, -0.05))

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
