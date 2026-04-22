""" pyplots.ai
network-force-directed: Force-Directed Graph
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_size_identity,
    theme,
    xlim,
    ylim,
)


# Set seed for reproducibility
np.random.seed(42)

# Data: Team collaboration network with 40 people across 4 departments
nodes = [
    # Engineering department (group 0)
    {"id": 0, "group": 0},
    {"id": 1, "group": 0},
    {"id": 2, "group": 0},
    {"id": 3, "group": 0},
    {"id": 4, "group": 0},
    {"id": 5, "group": 0},
    {"id": 6, "group": 0},
    {"id": 7, "group": 0},
    {"id": 8, "group": 0},
    {"id": 9, "group": 0},
    # Design department (group 1)
    {"id": 10, "group": 1},
    {"id": 11, "group": 1},
    {"id": 12, "group": 1},
    {"id": 13, "group": 1},
    {"id": 14, "group": 1},
    {"id": 15, "group": 1},
    {"id": 16, "group": 1},
    {"id": 17, "group": 1},
    {"id": 18, "group": 1},
    {"id": 19, "group": 1},
    # Marketing department (group 2)
    {"id": 20, "group": 2},
    {"id": 21, "group": 2},
    {"id": 22, "group": 2},
    {"id": 23, "group": 2},
    {"id": 24, "group": 2},
    {"id": 25, "group": 2},
    {"id": 26, "group": 2},
    {"id": 27, "group": 2},
    {"id": 28, "group": 2},
    {"id": 29, "group": 2},
    # Sales department (group 3)
    {"id": 30, "group": 3},
    {"id": 31, "group": 3},
    {"id": 32, "group": 3},
    {"id": 33, "group": 3},
    {"id": 34, "group": 3},
    {"id": 35, "group": 3},
    {"id": 36, "group": 3},
    {"id": 37, "group": 3},
    {"id": 38, "group": 3},
    {"id": 39, "group": 3},
]

# Edges with weights representing collaboration intensity
edges = [
    # Engineering internal (dense connections)
    (0, 1, 3),
    (0, 2, 2),
    (0, 3, 2),
    (1, 2, 3),
    (1, 4, 2),
    (2, 3, 2),
    (2, 5, 1),
    (3, 4, 3),
    (3, 6, 2),
    (4, 5, 2),
    (4, 7, 1),
    (5, 6, 3),
    (5, 8, 2),
    (6, 7, 2),
    (6, 9, 1),
    (7, 8, 3),
    (7, 9, 2),
    (8, 9, 2),
    (0, 9, 1),
    (1, 8, 1),
    # Design internal (dense connections)
    (10, 11, 3),
    (10, 12, 2),
    (10, 13, 2),
    (11, 12, 3),
    (11, 14, 2),
    (12, 13, 2),
    (12, 15, 1),
    (13, 14, 3),
    (13, 16, 2),
    (14, 15, 2),
    (14, 17, 1),
    (15, 16, 3),
    (15, 18, 2),
    (16, 17, 2),
    (16, 19, 1),
    (17, 18, 3),
    (17, 19, 2),
    (18, 19, 2),
    (10, 19, 1),
    (11, 18, 1),
    # Marketing internal (dense connections)
    (20, 21, 3),
    (20, 22, 2),
    (20, 23, 2),
    (21, 22, 3),
    (21, 24, 2),
    (22, 23, 2),
    (22, 25, 1),
    (23, 24, 3),
    (23, 26, 2),
    (24, 25, 2),
    (24, 27, 1),
    (25, 26, 3),
    (25, 28, 2),
    (26, 27, 2),
    (26, 29, 1),
    (27, 28, 3),
    (27, 29, 2),
    (28, 29, 2),
    (20, 29, 1),
    (21, 28, 1),
    # Sales internal (dense connections)
    (30, 31, 3),
    (30, 32, 2),
    (30, 33, 2),
    (31, 32, 3),
    (31, 34, 2),
    (32, 33, 2),
    (32, 35, 1),
    (33, 34, 3),
    (33, 36, 2),
    (34, 35, 2),
    (34, 37, 1),
    (35, 36, 3),
    (35, 38, 2),
    (36, 37, 2),
    (36, 39, 1),
    (37, 38, 3),
    (37, 39, 2),
    (38, 39, 2),
    (30, 39, 1),
    (31, 38, 1),
    # Cross-department bridges (weaker connections)
    (0, 10, 1),
    (2, 12, 1),
    (5, 15, 1),  # Engineering-Design
    (10, 20, 1),
    (14, 24, 1),
    (18, 28, 1),  # Design-Marketing
    (20, 30, 1),
    (23, 33, 1),
    (27, 37, 1),  # Marketing-Sales
    (9, 39, 1),
    (4, 34, 1),  # Engineering-Sales
    (3, 23, 1),
    (7, 27, 1),  # Engineering-Marketing
    (13, 33, 1),
    (16, 36, 1),  # Design-Sales
]

# Force-directed layout algorithm (Fruchterman-Reingold inspired)
n = len(nodes)
positions = np.random.rand(n, 2) * 2 - 1  # Random initial positions

# Algorithm parameters
k = 0.3  # Optimal spring length
iterations = 200
temperature = 1.0

for iteration in range(iterations):
    displacement = np.zeros((n, 2))

    # Repulsive forces: all nodes push each other apart
    for i in range(n):
        for j in range(i + 1, n):
            diff = positions[i] - positions[j]
            dist = max(np.linalg.norm(diff), 0.01)
            # Repulsive force inversely proportional to distance
            force_magnitude = (k * k) / dist
            force = force_magnitude * (diff / dist)
            displacement[i] += force
            displacement[j] -= force

    # Attractive forces: connected nodes pull together
    for src, tgt, weight in edges:
        diff = positions[src] - positions[tgt]
        dist = max(np.linalg.norm(diff), 0.01)
        # Attractive force proportional to distance, scaled by edge weight
        force_magnitude = (dist * dist / k) * (weight / 3)
        force = force_magnitude * (diff / dist)
        displacement[src] -= force
        displacement[tgt] += force

    # Apply displacement with simulated annealing (cooling)
    cooling = temperature * (1 - iteration / iterations)
    for i in range(n):
        disp_norm = np.linalg.norm(displacement[i])
        if disp_norm > 0:
            # Limit maximum displacement by temperature
            positions[i] += (displacement[i] / disp_norm) * min(disp_norm, cooling * 0.1)

# Normalize positions to [0.05, 0.95] range for plot margins
pos_min = positions.min(axis=0)
pos_max = positions.max(axis=0)
positions = (positions - pos_min) / (pos_max - pos_min + 1e-6) * 0.9 + 0.05
pos = {node["id"]: positions[i] for i, node in enumerate(nodes)}

# Calculate node degrees for sizing (more connections = larger node)
degrees = {node["id"]: 0 for node in nodes}
for src, tgt, _ in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Prepare data for plotnine
group_labels = {0: "Engineering", 1: "Design", 2: "Marketing", 3: "Sales"}
group_colors = {"Engineering": "#306998", "Design": "#FFD43B", "Marketing": "#4CAF50", "Sales": "#FF7043"}

# Create node dataframe
node_df = pd.DataFrame(
    {
        "x": [pos[node["id"]][0] for node in nodes],
        "y": [pos[node["id"]][1] for node in nodes],
        "group": [group_labels[node["group"]] for node in nodes],
        "size": [8 + degrees[node["id"]] * 1.5 for node in nodes],  # Scale for plotnine
    }
)

# Create edge dataframe with thickness based on weight
edge_data = []
for src, tgt, weight in edges:
    is_internal = nodes[src]["group"] == nodes[tgt]["group"]
    # Map weight (1-3) to line thickness (0.5-1.5 for internal, 0.8-1.8 for bridge)
    edge_thickness = 0.3 + weight * 0.4 if is_internal else 0.5 + weight * 0.4
    edge_data.append(
        {
            "x": pos[src][0],
            "y": pos[src][1],
            "xend": pos[tgt][0],
            "yend": pos[tgt][1],
            "weight": weight,
            "thickness": edge_thickness,
            "edge_type": "internal" if is_internal else "bridge",
        }
    )
edge_df = pd.DataFrame(edge_data)

# Separate internal and bridge edges for different styling
internal_edges = edge_df[edge_df["edge_type"] == "internal"]
bridge_edges = edge_df[edge_df["edge_type"] == "bridge"]

# Create the plot
plot = (
    ggplot()
    # Draw internal edges first (gray, thickness varies by weight)
    + geom_segment(
        data=internal_edges,
        mapping=aes(x="x", y="y", xend="xend", yend="yend", size="thickness"),
        color="#666666",
        alpha=0.6,
    )
    # Draw bridge edges (dashed, thickness varies by weight)
    + geom_segment(
        data=bridge_edges,
        mapping=aes(x="x", y="y", xend="xend", yend="yend", size="thickness"),
        color="#999999",
        alpha=0.7,
        linetype="dashed",
    )
    # Draw nodes on top, colored by department
    + geom_point(data=node_df, mapping=aes(x="x", y="y", color="group", size="size"), alpha=0.9, stroke=0.5)
    + scale_color_manual(values=group_colors)
    + scale_size_identity()
    + labs(title="network-force-directed · plotnine · pyplots.ai", color="Department")
    + xlim(-0.02, 1.02)
    + ylim(-0.02, 1.02)
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position=(0.02, 0.98),
        legend_background=element_rect(fill="white", alpha=0.9),
        # Remove axis elements for network graph
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_rect(fill="white"),
        plot_background=element_rect(fill="white"),
    )
)

# Save the plot
plot.save("plot.png", dpi=300)
