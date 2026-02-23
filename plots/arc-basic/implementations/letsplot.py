"""pyplots.ai
arc-basic: Basic Arc Diagram
Library: letsplot 4.8.2 | Python 3.14.3
Quality: /100 | Updated: 2026-02-23
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_alpha_identity,
    scale_color_identity,
    scale_size_identity,
    theme,
    xlim,
    ylim,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data: Character interactions in a story chapter
nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]
n_nodes = len(nodes)

# Edges: pairs of connected nodes with weights (source, target, weight)
edges = [
    (0, 1, 3),  # Alice-Bob (strong)
    (0, 3, 2),  # Alice-David
    (1, 2, 2),  # Bob-Carol
    (2, 4, 1),  # Carol-Eve
    (3, 5, 2),  # David-Frank
    (4, 6, 1),  # Eve-Grace
    (0, 7, 1),  # Alice-Henry (long-range)
    (1, 5, 2),  # Bob-Frank
    (2, 3, 3),  # Carol-David (strong)
    (5, 8, 1),  # Frank-Iris
    (6, 9, 2),  # Grace-Jack
    (0, 9, 1),  # Alice-Jack (longest range)
    (3, 7, 2),  # David-Henry
    (7, 8, 1),  # Henry-Iris
    (8, 9, 2),  # Iris-Jack
]

# Node positions along x-axis
x_positions = np.linspace(0, 1, n_nodes)
y_baseline = 0.08

# Count connections per node for visual hierarchy
connections = [0] * n_nodes
for s, t, w in edges:
    connections[s] += w
    connections[t] += w

# Arc color intensity by weight
weight_colors = {1: "#93B8CC", 2: "#306998", 3: "#1A3A5C"}
weight_alphas = {1: 0.5, 2: 0.65, 3: 0.8}
weight_labels = {1: "Weak", 2: "Moderate", 3: "Strong"}

# Create arc data for geom_path
arc_data = []
for edge_id, (start, end, weight) in enumerate(edges):
    x_start = x_positions[start]
    x_end = x_positions[end]

    # Arc height proportional to distance between nodes
    distance = abs(end - start)
    height = 0.08 * distance

    # Generate points along the arc
    n_points = 50
    t = np.linspace(0, np.pi, n_points)
    arc_x = x_start + (x_end - x_start) * (1 - np.cos(t)) / 2
    arc_y = y_baseline + height * np.sin(t)

    line_size = 1.0 + weight * 1.2
    color = weight_colors[weight]
    alpha = weight_alphas[weight]
    tooltip_text = f"{nodes[start]} \u2194 {nodes[end]}"
    strength = weight_labels[weight]

    for i in range(n_points):
        arc_data.append(
            {
                "x": arc_x[i],
                "y": arc_y[i],
                "edge_id": edge_id,
                "size": line_size,
                "color": color,
                "alpha": alpha,
                "connection": tooltip_text,
                "strength": strength,
            }
        )

arc_df = pd.DataFrame(arc_data)

# Node data with size based on total connection weight
max_conn = max(connections)
node_sizes = [6 + 10 * (c / max_conn) for c in connections]
node_df = pd.DataFrame(
    {"x": x_positions, "y": [y_baseline] * n_nodes, "name": nodes, "node_size": node_sizes, "connections": connections}
)

# Baseline segment data
baseline_df = pd.DataFrame({"x": [x_positions[0]], "xend": [x_positions[-1]], "y": [y_baseline], "yend": [y_baseline]})

# Label data (positioned below nodes)
label_df = pd.DataFrame({"x": x_positions, "y": [y_baseline - 0.045] * n_nodes, "name": nodes})

# Plot
plot = (
    ggplot()
    # Subtle baseline
    + geom_segment(data=baseline_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#D0D8E0", size=0.8)
    # Arcs with weight-based color, transparency, and tooltips
    + geom_path(
        data=arc_df,
        mapping=aes(x="x", y="y", group="edge_id", size="size", color="color", alpha="alpha"),
        tooltips=layer_tooltips().line("@connection").line("Strength: @strength"),
    )
    + scale_size_identity()
    + scale_color_identity()
    + scale_alpha_identity()
    # Nodes sized by connection weight with tooltips
    + geom_point(
        data=node_df,
        mapping=aes(x="x", y="y", size="node_size"),
        color="#1A3A5C",
        fill="#FFD43B",
        stroke=1.5,
        shape=21,
        tooltips=layer_tooltips().line("@name").line("Connections: @connections"),
    )
    + scale_size_identity()
    # Node labels
    + geom_text(
        data=label_df, mapping=aes(x="x", y="y", label="name"), size=16, color="#1A3A5C", fontface="bold", vjust=1
    )
    # Styling
    + xlim(-0.06, 1.06)
    + ylim(-0.15, 0.85)
    + labs(title="Character Interactions \u00b7 arc-basic \u00b7 letsplot \u00b7 pyplots.ai")
    + theme(
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_rect(fill="white", color="white"),
        plot_background=element_rect(fill="white", color="white"),
        plot_title=element_text(size=24, face="bold", color="#1A3A5C"),
        legend_position="none",
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
