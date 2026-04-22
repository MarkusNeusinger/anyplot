""" pyplots.ai
sankey-basic: Basic Sankey Diagram
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import sys


# Prevent current directory from shadowing the plotnine package
sys.path = [p for p in sys.path if not p.endswith("implementations")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_text,
    geom_polygon,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Data - Energy flow from sources to sectors
flows = pd.DataFrame(
    {
        "source": ["Coal", "Coal", "Gas", "Gas", "Gas", "Nuclear", "Nuclear", "Renewables", "Renewables"],
        "target": [
            "Industrial",
            "Residential",
            "Industrial",
            "Commercial",
            "Residential",
            "Commercial",
            "Residential",
            "Commercial",
            "Residential",
        ],
        "value": [35, 15, 25, 20, 15, 18, 12, 8, 12],
    }
)

# Define node positions
sources = ["Coal", "Gas", "Nuclear", "Renewables"]
targets = ["Industrial", "Commercial", "Residential"]

# X positions with margins for labels
x_left = 0.2
x_right = 0.8
node_width = 0.08
node_gap = 0.03

# Calculate node sizes based on total flow
source_totals = flows.groupby("source")["value"].sum().to_dict()
target_totals = flows.groupby("target")["value"].sum().to_dict()
total_flow = flows["value"].sum()

# Calculate source node positions (left side)
source_positions = {}
current_y = 1.0
for src in sources:
    height = source_totals[src] / total_flow * 0.8
    source_positions[src] = {
        "x": x_left,
        "y_top": current_y,
        "y_bottom": current_y - height,
        "height": height,
        "flow_offset": 0,
    }
    current_y = current_y - height - node_gap

# Calculate target node positions (right side)
target_positions = {}
current_y = 1.0
for tgt in targets:
    height = target_totals[tgt] / total_flow * 0.8
    target_positions[tgt] = {
        "x": x_right,
        "y_top": current_y,
        "y_bottom": current_y - height,
        "height": height,
        "flow_offset": 0,
    }
    current_y = current_y - height - node_gap

# Color map for nodes - sources get their own colors, targets get distinct colors
source_colors = {"Coal": "#306998", "Gas": "#FFD43B", "Nuclear": "#4ECDC4", "Renewables": "#2ECC71"}
target_colors = {"Industrial": "#E74C3C", "Commercial": "#9B59B6", "Residential": "#F39C12"}

# Build node rectangles dataframe - each node gets its own color
node_data = []
for src in sources:
    pos = source_positions[src]
    node_data.append(
        {
            "name": src,
            "xmin": pos["x"],
            "xmax": pos["x"] + node_width,
            "ymin": pos["y_bottom"],
            "ymax": pos["y_top"],
            "label_x": pos["x"] - 0.02,
            "label_y": (pos["y_top"] + pos["y_bottom"]) / 2,
            "side": "source",
            "node_color": src,
        }
    )

for tgt in targets:
    pos = target_positions[tgt]
    node_data.append(
        {
            "name": tgt,
            "xmin": pos["x"] - node_width,
            "xmax": pos["x"],
            "ymin": pos["y_bottom"],
            "ymax": pos["y_top"],
            "label_x": pos["x"] + 0.02,
            "label_y": (pos["y_top"] + pos["y_bottom"]) / 2,
            "side": "target",
            "node_color": tgt,
        }
    )

nodes_df = pd.DataFrame(node_data)


# Build flow polygons (curved paths between nodes)
flow_polygons = []
flow_labels = []  # Track center positions for flow value labels
for _, row in flows.iterrows():
    src = row["source"]
    tgt = row["target"]
    val = row["value"]

    # Calculate flow thickness
    flow_height = val / total_flow * 0.8

    # Source connection point
    src_pos = source_positions[src]
    src_y_top = src_pos["y_top"] - src_pos["flow_offset"]
    src_y_bottom = src_y_top - flow_height
    src_pos["flow_offset"] += flow_height

    # Target connection point
    tgt_pos = target_positions[tgt]
    tgt_y_top = tgt_pos["y_top"] - tgt_pos["flow_offset"]
    tgt_y_bottom = tgt_y_top - flow_height
    tgt_pos["flow_offset"] += flow_height

    # Create curved flow polygon using smooth interpolation
    flow_x_left = x_left + node_width
    flow_x_right = x_right - node_width
    n_points = 50

    # Top edge (left to right)
    t = np.linspace(0, 1, n_points)
    x_top = flow_x_left + (flow_x_right - flow_x_left) * t
    y_top = src_y_top + (tgt_y_top - src_y_top) * (3 * t**2 - 2 * t**3)

    # Bottom edge (right to left)
    x_bottom = flow_x_right + (flow_x_left - flow_x_right) * t
    y_bottom = tgt_y_bottom + (src_y_bottom - tgt_y_bottom) * (3 * t**2 - 2 * t**3)

    # Combine into polygon
    x_polygon = np.concatenate([x_top, x_bottom])
    y_polygon = np.concatenate([y_top, y_bottom])

    for i in range(len(x_polygon)):
        flow_polygons.append({"x": x_polygon[i], "y": y_polygon[i], "flow_id": f"{src}_{tgt}", "source": src})

    # Store center position for flow label (slightly offset from center based on source index)
    # This helps avoid label overlap when flows cross
    mid_idx = n_points // 2
    flow_center_y = (y_top[mid_idx] + y_bottom[n_points - 1 - mid_idx]) / 2
    src_idx = sources.index(src)
    label_x_offset = 0.35 + src_idx * 0.1  # Stagger labels across flow width
    flow_labels.append({"x": label_x_offset, "y": flow_center_y, "value": str(val), "flow_height": flow_height})

flows_df = pd.DataFrame(flow_polygons)
flow_labels_df = pd.DataFrame(flow_labels)

# Create the plot
plot = (
    ggplot()
    # Flow polygons with transparency
    + geom_polygon(flows_df, aes(x="x", y="y", group="flow_id", fill="source"), alpha=0.5)
    # Node rectangles with individual colors
    + geom_rect(
        nodes_df, aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="node_color"), color="white", size=0.5
    )
    # Flow value labels (only for larger flows to avoid clutter)
    + geom_text(
        flow_labels_df[flow_labels_df["flow_height"] >= 0.05],
        aes(x="x", y="y", label="value"),
        ha="center",
        va="center",
        size=11,
        color="#333333",
        fontweight="bold",
    )
    # Source labels (right-aligned) - increased font size
    + geom_text(
        nodes_df[nodes_df["side"] == "source"],
        aes(x="label_x", y="label_y", label="name"),
        ha="right",
        size=16,
        color="#333333",
        fontweight="bold",
    )
    # Target labels (left-aligned) - increased font size
    + geom_text(
        nodes_df[nodes_df["side"] == "target"],
        aes(x="label_x", y="label_y", label="name"),
        ha="left",
        size=16,
        color="#333333",
        fontweight="bold",
    )
    # Color scales - sources for flows, all nodes for rectangles
    + scale_fill_manual(
        values={
            # Source colors (for flows and source nodes)
            "Coal": "#306998",
            "Gas": "#FFD43B",
            "Nuclear": "#4ECDC4",
            "Renewables": "#2ECC71",
            # Target colors (for target nodes)
            "Industrial": "#E74C3C",
            "Commercial": "#9B59B6",
            "Residential": "#F39C12",
        }
    )
    + labs(title="Energy Flow · sankey-basic · plotnine · pyplots.ai", x="", y="")
    + coord_cartesian(xlim=(-0.05, 1.1))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        legend_position="none",
    )
    + annotate("text", x=x_left + node_width / 2, y=-0.05, label="Sources", size=16, color="#555555", fontweight="bold")
    + annotate(
        "text", x=x_right - node_width / 2, y=-0.05, label="Sectors", size=16, color="#555555", fontweight="bold"
    )
)

plot.save("plot.png", dpi=300, verbose=False)
