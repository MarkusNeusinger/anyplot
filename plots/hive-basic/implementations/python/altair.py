""" pyplots.ai
hive-basic: Basic Hive Plot
Library: altair 6.0.0 | Python 3.13.11
Quality: 78/100 | Created: 2025-12-24
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Software module dependency network

# Define nodes with module types (axis assignment) and importance (position on axis)
# Wider spacing on Core axis to avoid label crowding
nodes_data = [
    # Core modules (axis 0) - foundational components - wider spacing
    {"id": "core_main", "name": "Main", "axis": "Core", "importance": 1.0},
    {"id": "core_db", "name": "Database", "axis": "Core", "importance": 0.80},
    {"id": "core_config", "name": "Config", "axis": "Core", "importance": 0.60},
    {"id": "core_logger", "name": "Logger", "axis": "Core", "importance": 0.40},
    {"id": "core_cache", "name": "Cache", "axis": "Core", "importance": 0.20},
    # Utility modules (axis 1) - helper components
    {"id": "util_http", "name": "HTTP", "axis": "Utility", "importance": 1.0},
    {"id": "util_file", "name": "FileIO", "axis": "Utility", "importance": 0.75},
    {"id": "util_string", "name": "String", "axis": "Utility", "importance": 0.50},
    {"id": "util_date", "name": "DateTime", "axis": "Utility", "importance": 0.25},
    # Interface modules (axis 2) - external-facing components
    {"id": "iface_api", "name": "REST API", "axis": "Interface", "importance": 1.0},
    {"id": "iface_web", "name": "WebUI", "axis": "Interface", "importance": 0.66},
    {"id": "iface_cli", "name": "CLI", "axis": "Interface", "importance": 0.33},
]

# Define edges (dependencies between modules)
edges_data = [
    # Core to Utility connections
    ("core_main", "util_string"),
    ("core_main", "util_file"),
    ("core_config", "util_file"),
    ("core_config", "util_string"),
    ("core_logger", "util_date"),
    ("core_logger", "util_file"),
    ("core_cache", "util_date"),
    ("core_db", "util_string"),
    # Core to Interface connections
    ("core_main", "iface_api"),
    ("core_main", "iface_cli"),
    ("core_config", "iface_api"),
    ("core_db", "iface_api"),
    ("core_logger", "iface_web"),
    # Utility to Interface connections
    ("util_http", "iface_api"),
    ("util_http", "iface_web"),
    ("util_string", "iface_cli"),
    ("util_file", "iface_cli"),
    ("util_date", "iface_web"),
]

# Convert to DataFrame
nodes_df = pd.DataFrame(nodes_data)

# Axis configuration - centered on canvas with 120-degree separation
# Rotated to place Core at upper-right, balancing visual weight across canvas
axis_config = {
    "Core": {"angle": 30, "color": "#306998"},  # Python Blue - upper right
    "Utility": {"angle": 150, "color": "#FFD43B"},  # Python Yellow - upper left
    "Interface": {"angle": 270, "color": "#4ECDC4"},  # Teal - bottom center
}

# Calculate node positions - inline polar to Cartesian conversion
min_radius = 0.25
max_radius = 0.85

node_positions = {}
nodes_df["x"] = 0.0
nodes_df["y"] = 0.0

for idx, row in nodes_df.iterrows():
    axis = row["axis"]
    angle_rad = np.radians(axis_config[axis]["angle"])
    radius = min_radius + (max_radius - min_radius) * row["importance"]
    nodes_df.at[idx, "x"] = radius * np.cos(angle_rad)
    nodes_df.at[idx, "y"] = radius * np.sin(angle_rad)
    nodes_df.at[idx, "color"] = axis_config[axis]["color"]
    node_positions[row["id"]] = (nodes_df.at[idx, "x"], nodes_df.at[idx, "y"])

# Create edges DataFrame with start and end coordinates
edges_list = []
for source, target in edges_data:
    if source in node_positions and target in node_positions:
        x1, y1 = node_positions[source]
        x2, y2 = node_positions[target]
        source_axis = nodes_df[nodes_df["id"] == source]["axis"].values[0]
        target_axis = nodes_df[nodes_df["id"] == target]["axis"].values[0]
        edges_list.append(
            {
                "x": x1,
                "y": y1,
                "x2": x2,
                "y2": y2,
                "source": source,
                "target": target,
                "connection": f"{source_axis} → {target_axis}",
            }
        )

edges_df = pd.DataFrame(edges_list)

# Create axis lines (from center outward)
axis_lines = []
for axis_name, config in axis_config.items():
    angle_rad = np.radians(config["angle"])
    axis_lines.append(
        {"x": 0, "y": 0, "x2": 0.95 * np.cos(angle_rad), "y2": 0.95 * np.sin(angle_rad), "axis": axis_name}
    )
axis_df = pd.DataFrame(axis_lines)

# Create axis labels - positioned at end of axes with proper offsets
axis_labels = []
for axis_name, config in axis_config.items():
    angle_rad = np.radians(config["angle"])
    # Larger offset for axis labels to avoid overlap with node labels
    label_dist = 1.12
    axis_labels.append({"x": label_dist * np.cos(angle_rad), "y": label_dist * np.sin(angle_rad), "label": axis_name})
axis_labels_df = pd.DataFrame(axis_labels)

# Create legend data for the three module types
legend_data = pd.DataFrame(
    [
        {"axis": "Core", "description": "Core: Foundational modules"},
        {"axis": "Utility", "description": "Utility: Helper components"},
        {"axis": "Interface", "description": "Interface: External-facing"},
    ]
)

# Plot: Layer edges, axis lines, nodes, and labels

# Edge lines with transparency
edges_chart = (
    alt.Chart(edges_df)
    .mark_rule(strokeWidth=2, opacity=0.35, color="#666666")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-1.2, 1.2]), axis=None),
        y=alt.Y("y:Q", scale=alt.Scale(domain=[-1.2, 1.2]), axis=None),
        x2="x2:Q",
        y2="y2:Q",
        tooltip=["source:N", "target:N", "connection:N"],
    )
)

# Axis lines
axis_chart = (
    alt.Chart(axis_df)
    .mark_rule(strokeWidth=4, opacity=0.7)
    .encode(
        x="x:Q",
        y="y:Q",
        x2="x2:Q",
        y2="y2:Q",
        color=alt.Color(
            "axis:N",
            scale=alt.Scale(domain=["Core", "Utility", "Interface"], range=["#306998", "#FFD43B", "#4ECDC4"]),
            legend=None,
        ),
    )
)

# Nodes - larger size for visibility
nodes_chart = (
    alt.Chart(nodes_df)
    .mark_circle(size=600, opacity=0.95, stroke="white", strokeWidth=3)
    .encode(
        x="x:Q",
        y="y:Q",
        color=alt.Color(
            "axis:N",
            scale=alt.Scale(domain=["Core", "Utility", "Interface"], range=["#306998", "#FFD43B", "#4ECDC4"]),
            legend=None,
        ),
        tooltip=["name:N", "axis:N", "importance:Q"],
    )
)

# Node labels - calculated offsets based on axis direction to avoid overlap
node_labels_data = nodes_df.copy()
label_offset = 0.12

for idx, row in node_labels_data.iterrows():
    axis = row["axis"]
    if axis == "Core":
        # Core axis at 30 degrees (upper right) - labels to the right
        node_labels_data.at[idx, "label_x"] = row["x"] + label_offset
        node_labels_data.at[idx, "label_y"] = row["y"]
        node_labels_data.at[idx, "align"] = "left"
    elif axis == "Utility":
        # Utility axis at 150 degrees (upper left) - labels to the left
        node_labels_data.at[idx, "label_x"] = row["x"] - label_offset
        node_labels_data.at[idx, "label_y"] = row["y"]
        node_labels_data.at[idx, "align"] = "right"
    else:  # Interface
        # Interface axis at 270 degrees (bottom center) - labels alternating left/right
        # Alternate sides based on importance to spread labels out
        if row["importance"] > 0.5:
            node_labels_data.at[idx, "label_x"] = row["x"] + label_offset
            node_labels_data.at[idx, "align"] = "left"
        else:
            node_labels_data.at[idx, "label_x"] = row["x"] - label_offset
            node_labels_data.at[idx, "align"] = "right"
        node_labels_data.at[idx, "label_y"] = row["y"]

node_labels = (
    alt.Chart(node_labels_data)
    .mark_text(fontSize=18, fontWeight="bold")
    .encode(x="label_x:Q", y="label_y:Q", text="name:N", color=alt.value("#222222"))
)

# Axis labels - larger font with explicit color mapping for visibility
axis_label_chart = (
    alt.Chart(axis_labels_df)
    .mark_text(fontSize=36, fontWeight="bold")
    .encode(
        x="x:Q",
        y="y:Q",
        text="label:N",
        color=alt.Color(
            "label:N",
            scale=alt.Scale(domain=["Core", "Utility", "Interface"], range=["#306998", "#B8860B", "#2E8B8B"]),
            legend=None,
        ),
    )
)

# Legend in corner showing the three module types
legend_chart = (
    alt.Chart(legend_data)
    .mark_point(size=400, filled=True)
    .encode(
        y=alt.Y("axis:N", title=None, axis=alt.Axis(labelFontSize=20, labelFontWeight="bold")),
        color=alt.Color(
            "axis:N",
            scale=alt.Scale(domain=["Core", "Utility", "Interface"], range=["#306998", "#FFD43B", "#4ECDC4"]),
            legend=None,
        ),
    )
    .properties(title=alt.Title("Module Types", fontSize=22), width=50, height=100)
)

# Combine all layers for hive plot
hive_chart = (edges_chart + axis_chart + nodes_chart + node_labels + axis_label_chart).properties(
    width=900,
    height=900,
    title=alt.Title(
        text="hive-basic · altair · pyplots.ai",
        subtitle="Software Module Dependency Network",
        fontSize=32,
        subtitleFontSize=22,
        anchor="middle",
    ),
)

# Combine hive plot with legend (horizontal concatenation)
chart = alt.hconcat(hive_chart, legend_chart, spacing=40).configure_view(strokeWidth=0).configure_axis(grid=False)

# Save - square format for radial plot (3600x3600 at scale 4)
chart.save("plot.png", scale_factor=4.0)
chart.save("plot.html")
