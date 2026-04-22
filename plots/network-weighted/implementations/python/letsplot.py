""" pyplots.ai
network-weighted: Weighted Network Graph with Edge Thickness
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()
np.random.seed(42)

# Create trade network: 15 countries with weighted trade relationships
countries = [
    "USA",
    "China",
    "Germany",
    "Japan",
    "UK",
    "France",
    "Canada",
    "Mexico",
    "Brazil",
    "India",
    "S.Korea",
    "Italy",
    "Australia",
    "Spain",
    "Netherlands",
]
n_nodes = len(countries)

# Generate edges with weights (bilateral trade in billions USD)
edges_data = []
edge_pairs = [
    (0, 1, 550),
    (0, 2, 180),
    (0, 3, 220),
    (0, 4, 140),
    (0, 6, 380),
    (0, 7, 420),
    (0, 9, 95),
    (0, 10, 130),
    (1, 2, 200),
    (1, 3, 340),
    (1, 4, 85),
    (1, 10, 290),
    (1, 12, 160),
    (2, 3, 55),
    (2, 4, 150),
    (2, 5, 180),
    (2, 8, 45),
    (2, 13, 65),
    (2, 14, 220),
    (3, 4, 35),
    (3, 10, 85),
    (3, 12, 70),
    (4, 5, 95),
    (4, 11, 55),
    (4, 14, 80),
    (5, 11, 85),
    (5, 13, 95),
    (6, 7, 75),
    (7, 8, 40),
    (8, 9, 30),
    (9, 12, 25),
    (11, 13, 45),
    (12, 14, 35),
]

for src, tgt, weight in edge_pairs:
    edges_data.append({"source": src, "target": tgt, "weight": weight})

# Calculate positions using spring layout (simple force-directed simulation)
pos = np.zeros((n_nodes, 2))
# Initial positions in a circle
angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)
pos[:, 0] = np.cos(angles)
pos[:, 1] = np.sin(angles)

# Simple force-directed iterations
for _ in range(100):
    forces = np.zeros_like(pos)

    # Repulsion between all nodes
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            diff = pos[i] - pos[j]
            dist = max(np.linalg.norm(diff), 0.1)
            force = diff / (dist**2) * 0.5
            forces[i] += force
            forces[j] -= force

    # Attraction along edges (weighted)
    for edge in edges_data:
        i, j = edge["source"], edge["target"]
        diff = pos[j] - pos[i]
        dist = np.linalg.norm(diff)
        weight_factor = np.log1p(edge["weight"]) * 0.001
        force = diff * weight_factor
        forces[i] += force
        forces[j] -= force

    # Apply forces with damping
    pos += forces * 0.1

    # Center
    pos -= pos.mean(axis=0)

# Scale positions with margin for labels (reduce scale to leave space at boundaries)
pos = pos / np.abs(pos).max() * 3.2

# Calculate weighted degree for node sizing
weighted_degree = np.zeros(n_nodes)
for edge in edges_data:
    weighted_degree[edge["source"]] += edge["weight"]
    weighted_degree[edge["target"]] += edge["weight"]

# Create node dataframe
nodes_df = pd.DataFrame({"x": pos[:, 0], "y": pos[:, 1], "label": countries, "weighted_degree": weighted_degree})

# Create edges dataframe with line segments
edges_list = []
for edge in edges_data:
    src, tgt = edge["source"], edge["target"]
    edges_list.append(
        {"x": pos[src, 0], "y": pos[src, 1], "xend": pos[tgt, 0], "yend": pos[tgt, 1], "weight": edge["weight"]}
    )

edges_df = pd.DataFrame(edges_list)

# Normalize edge weights for line width (1 to 8 range)
min_w, max_w = edges_df["weight"].min(), edges_df["weight"].max()
edges_df["line_width"] = 1 + (edges_df["weight"] - min_w) / (max_w - min_w) * 7

# Normalize node sizes (6 to 18 range for better visibility)
min_d, max_d = nodes_df["weighted_degree"].min(), nodes_df["weighted_degree"].max()
nodes_df["node_size"] = 6 + (nodes_df["weighted_degree"] - min_d) / (max_d - min_d) * 12

# Create the plot
plot = (
    ggplot()
    # Edges as segments with varying width based on weight
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend", size="weight"), data=edges_df, color="#888888", alpha=0.6
    )
    # Scale for edge thickness
    + scale_size(range=[1, 10], name="Trade Volume\n(Billions USD)")
    # Nodes as points sized by weighted degree (Python colors)
    + geom_point(aes(x="x", y="y", size="node_size"), data=nodes_df, color="#306998", alpha=0.95, show_legend=False)
    # Node labels
    + geom_text(aes(x="x", y="y", label="label"), data=nodes_df, size=14, color="#1a1a1a", nudge_y=0.4, fontface="bold")
    # Styling
    + labs(
        title="network-weighted · letsplot · pyplots.ai",
        subtitle="International Trade Network (Edge Thickness = Trade Volume)",
    )
    # Explicit axis limits to prevent label clipping
    + scale_x_continuous(limits=[-5, 5])
    + scale_y_continuous(limits=[-5, 5])
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28),
        plot_subtitle=element_text(size=18),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position=[0.95, 0.25],
        legend_justification=[1, 0.5],
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scaled 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactive version
ggsave(plot, "plot.html", path=".")
