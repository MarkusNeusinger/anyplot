""" pyplots.ai
hive-basic: Basic Hive Plot
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 82/100 | Created: 2025-12-24
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_void,
    xlim,
    ylim,
)


# Set seed for reproducibility
np.random.seed(42)

# Create sample software module dependency network
# Nodes: modules categorized by type (core, utility, interface)
# Balanced distribution: 7 core, 7 utility, 7 interface = 21 nodes
nodes = pd.DataFrame(
    {
        "id": [
            # Core modules (7)
            "auth",
            "db",
            "core",
            "session",
            "kernel",
            "runtime",
            "engine",
            # Utility modules (7)
            "cache",
            "logger",
            "config",
            "validator",
            "crypto",
            "parser",
            "queue",
            # Interface modules (7)
            "api",
            "web",
            "cli",
            "router",
            "http",
            "grpc",
            "websocket",
        ],
        "category": [
            "core",
            "core",
            "core",
            "core",
            "core",
            "core",
            "core",
            "utility",
            "utility",
            "utility",
            "utility",
            "utility",
            "utility",
            "utility",
            "interface",
            "interface",
            "interface",
            "interface",
            "interface",
            "interface",
            "interface",
        ],
        "degree": [8, 7, 9, 6, 5, 4, 6, 5, 6, 4, 5, 4, 3, 4, 6, 5, 4, 5, 5, 3, 4],
    }
)

# Edges: dependencies between modules
edges = pd.DataFrame(
    {
        "source": [
            "api",
            "api",
            "api",
            "web",
            "web",
            "web",
            "cli",
            "cli",
            "auth",
            "auth",
            "auth",
            "db",
            "db",
            "cache",
            "logger",
            "config",
            "validator",
            "core",
            "core",
            "core",
            "router",
            "router",
            "session",
            "session",
            "http",
            "crypto",
            "grpc",
            "websocket",
            "kernel",
            "runtime",
        ],
        "target": [
            "auth",
            "db",
            "logger",
            "auth",
            "session",
            "router",
            "config",
            "logger",
            "db",
            "crypto",
            "session",
            "cache",
            "logger",
            "logger",
            "config",
            "validator",
            "logger",
            "db",
            "cache",
            "logger",
            "http",
            "auth",
            "cache",
            "crypto",
            "parser",
            "parser",
            "auth",
            "session",
            "runtime",
            "engine",
        ],
    }
)

# Hive plot parameters
# 3 axes for the 3 categories
axis_angles = {"core": 90, "utility": 210, "interface": 330}  # degrees
axis_colors = {"core": "#306998", "utility": "#FFD43B", "interface": "#4ECDC4"}

# Calculate node positions on axes
max_degree = nodes["degree"].max()

# Count nodes per category for spacing
category_counts = nodes.groupby("category").cumcount()
category_totals = nodes.groupby("category")["id"].transform("count")

nodes["idx_in_axis"] = category_counts
nodes["count_in_axis"] = category_totals

# Calculate positions for each node (flat code, no function)
positions = []
for _, row in nodes.iterrows():
    angle_deg = axis_angles[row["category"]]
    angle_rad = np.radians(angle_deg)

    # Normalize degree to radial distance (0.25 to 0.90 of axis length)
    # Space nodes more evenly along axis using index-based positioning
    base_radius = 0.25 + (row["idx_in_axis"] / max(row["count_in_axis"] - 1, 1)) * 0.65

    x = base_radius * np.cos(angle_rad)
    y = base_radius * np.sin(angle_rad)

    # Calculate node size based on degree (min 4, max 12)
    node_size = 4 + (row["degree"] / max_degree) * 8

    positions.append(
        {"id": row["id"], "x": x, "y": y, "category": row["category"], "degree": row["degree"], "node_size": node_size}
    )

node_positions = pd.DataFrame(positions)

# Create axis lines data (from center to edge)
axis_lines = []
for cat, angle in axis_angles.items():
    angle_rad = np.radians(angle)
    axis_lines.append(
        {"x": 0, "y": 0, "xend": 1.0 * np.cos(angle_rad), "yend": 1.0 * np.sin(angle_rad), "category": cat}
    )
axis_df = pd.DataFrame(axis_lines)

# Create edge data with Bezier curves
edge_data = []
for _, row in edges.iterrows():
    src_match = node_positions[node_positions["id"] == row["source"]]
    tgt_match = node_positions[node_positions["id"] == row["target"]]

    if len(src_match) == 0 or len(tgt_match) == 0:
        continue

    src_pos = src_match.iloc[0]
    tgt_pos = tgt_match.iloc[0]

    src_cat = src_pos["category"]
    tgt_cat = tgt_pos["category"]

    # Determine curve control point based on edge type
    if src_cat == tgt_cat:
        # Same axis: curve inward toward center
        mid_factor = 0.3
    else:
        # Different axes: curve through center area
        mid_factor = 0.15

    # Control point toward center
    ctrl_x = mid_factor * (src_pos["x"] + tgt_pos["x"]) / 2
    ctrl_y = mid_factor * (src_pos["y"] + tgt_pos["y"]) / 2

    # Generate points along quadratic Bezier curve
    n_points = 20
    for i in range(n_points):
        t0 = i / n_points
        t1 = (i + 1) / n_points

        # Quadratic Bezier: B(t) = (1-t)^2*P0 + 2*(1-t)*t*P1 + t^2*P2
        x0 = (1 - t0) ** 2 * src_pos["x"] + 2 * (1 - t0) * t0 * ctrl_x + t0**2 * tgt_pos["x"]
        y0 = (1 - t0) ** 2 * src_pos["y"] + 2 * (1 - t0) * t0 * ctrl_y + t0**2 * tgt_pos["y"]
        x1 = (1 - t1) ** 2 * src_pos["x"] + 2 * (1 - t1) * t1 * ctrl_x + t1**2 * tgt_pos["x"]
        y1 = (1 - t1) ** 2 * src_pos["y"] + 2 * (1 - t1) * t1 * ctrl_y + t1**2 * tgt_pos["y"]

        edge_data.append(
            {
                "x": x0,
                "y": y0,
                "xend": x1,
                "yend": y1,
                "src_cat": src_cat,
                "tgt_cat": tgt_cat,
                "edge_color": axis_colors[src_cat],
            }
        )

edge_df = pd.DataFrame(edge_data)

# Create axis labels
axis_labels = []
for cat, angle in axis_angles.items():
    angle_rad = np.radians(angle)
    axis_labels.append(
        {"x": 1.12 * np.cos(angle_rad), "y": 1.12 * np.sin(angle_rad), "label": cat.upper(), "category": cat}
    )
label_df = pd.DataFrame(axis_labels)

# Create node labels offset from node positions
node_labels = []
for _, row in node_positions.iterrows():
    angle_deg = axis_angles[row["category"]]
    angle_rad = np.radians(angle_deg)

    # Offset label perpendicular to axis (to avoid overlap with axis line)
    # Use larger offset for better visibility
    offset = 0.12
    perp_angle = angle_rad + np.pi / 2  # perpendicular direction
    label_x = row["x"] + offset * np.cos(perp_angle)
    label_y = row["y"] + offset * np.sin(perp_angle)

    node_labels.append({"x": label_x, "y": label_y, "label": row["id"], "category": row["category"]})
node_labels_df = pd.DataFrame(node_labels)

# Create the plot
plot = (
    ggplot()
    # Draw edges first (behind nodes) colored by source category
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend", color="src_cat"), data=edge_df, size=1.2, alpha=0.6)
    # Draw axis lines
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend", color="category"), data=axis_df, size=3, alpha=0.8)
    # Draw nodes with size based on degree
    + geom_point(aes(x="x", y="y", color="category", size="node_size"), data=node_positions, alpha=0.95)
    # Add node labels (module names) with larger size and white background effect
    + geom_text(aes(x="x", y="y", label="label"), data=node_labels_df, size=11, color="#1a1a1a", fontweight="bold")
    # Add axis category labels
    + geom_text(aes(x="x", y="y", label="label", color="category"), data=label_df, size=16, fontweight="bold")
    # Color scale
    + scale_color_manual(values=axis_colors)
    # Styling
    + coord_fixed(ratio=1)
    + xlim(-1.5, 1.5)
    + ylim(-1.5, 1.5)
    + labs(
        title="hive-basic · plotnine · pyplots.ai",
        subtitle="Node size indicates connection degree (larger = more connections)",
    )
    + theme_void()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        plot_subtitle=element_text(size=14, ha="center", color="#555555"),
        legend_position="none",
        plot_margin=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
