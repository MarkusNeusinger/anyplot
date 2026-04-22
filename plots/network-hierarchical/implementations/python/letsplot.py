""" pyplots.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

np.random.seed(42)

# Data: Small tech company organizational chart with 30 employees across 4 levels
# Level 0: CEO (1)
# Level 1: VPs (3)
# Level 2: Managers (8)
# Level 3: Individual Contributors (18)

nodes = [
    # Level 0 - CEO
    {"id": 0, "label": "CEO", "level": 0, "parent": None},
    # Level 1 - VPs
    {"id": 1, "label": "VP Eng", "level": 1, "parent": 0},
    {"id": 2, "label": "VP Sales", "level": 1, "parent": 0},
    {"id": 3, "label": "VP Ops", "level": 1, "parent": 0},
    # Level 2 - Managers under VP Engineering
    {"id": 4, "label": "Mgr FE", "level": 2, "parent": 1},
    {"id": 5, "label": "Mgr BE", "level": 2, "parent": 1},
    {"id": 6, "label": "Mgr QA", "level": 2, "parent": 1},
    # Level 2 - Managers under VP Sales
    {"id": 7, "label": "Mgr West", "level": 2, "parent": 2},
    {"id": 8, "label": "Mgr East", "level": 2, "parent": 2},
    # Level 2 - Managers under VP Ops
    {"id": 9, "label": "Mgr HR", "level": 2, "parent": 3},
    {"id": 10, "label": "Mgr IT", "level": 2, "parent": 3},
    {"id": 11, "label": "Mgr Fin", "level": 2, "parent": 3},
    # Level 3 - Engineers under Mgr FE
    {"id": 12, "label": "Dev 1", "level": 3, "parent": 4},
    {"id": 13, "label": "Dev 2", "level": 3, "parent": 4},
    {"id": 14, "label": "Dev 3", "level": 3, "parent": 4},
    # Level 3 - Engineers under Mgr BE
    {"id": 15, "label": "Dev 4", "level": 3, "parent": 5},
    {"id": 16, "label": "Dev 5", "level": 3, "parent": 5},
    {"id": 17, "label": "Dev 6", "level": 3, "parent": 5},
    # Level 3 - QA under Mgr QA
    {"id": 18, "label": "QA 1", "level": 3, "parent": 6},
    {"id": 19, "label": "QA 2", "level": 3, "parent": 6},
    # Level 3 - Sales reps under Mgr West
    {"id": 20, "label": "Rep 1", "level": 3, "parent": 7},
    {"id": 21, "label": "Rep 2", "level": 3, "parent": 7},
    # Level 3 - Sales reps under Mgr East
    {"id": 22, "label": "Rep 3", "level": 3, "parent": 8},
    {"id": 23, "label": "Rep 4", "level": 3, "parent": 8},
    {"id": 24, "label": "Rep 5", "level": 3, "parent": 8},
    # Level 3 - Ops staff under HR
    {"id": 25, "label": "HR 1", "level": 3, "parent": 9},
    # Level 3 - IT staff
    {"id": 26, "label": "IT 1", "level": 3, "parent": 10},
    {"id": 27, "label": "IT 2", "level": 3, "parent": 10},
    # Level 3 - Finance staff
    {"id": 28, "label": "Fin 1", "level": 3, "parent": 11},
    {"id": 29, "label": "Fin 2", "level": 3, "parent": 11},
]

# Build edges from parent-child relationships
edges = [(node["parent"], node["id"]) for node in nodes if node["parent"] is not None]

# Build tree structure for layout calculation
children = {node["id"]: [] for node in nodes}
for parent, child in edges:
    children[parent].append(child)

# Calculate x positions using a tree layout algorithm (similar to Reingold-Tilford)
# We assign horizontal positions based on leaf counts and subtree widths
x_pos = {}
y_pos = {}


def count_leaves(node_id):
    """Count number of leaf nodes in subtree."""
    if not children[node_id]:
        return 1
    return sum(count_leaves(c) for c in children[node_id])


def assign_x_positions(node_id, left_bound, right_bound):
    """Assign x positions recursively, centering parents over children."""
    if not children[node_id]:
        # Leaf node: place in center of its allocated space
        x_pos[node_id] = (left_bound + right_bound) / 2
        return

    # Calculate total leaves for proportional spacing
    child_leaves = [(c, count_leaves(c)) for c in children[node_id]]
    total_leaves = sum(leaves for _, leaves in child_leaves)

    # Assign positions to children
    current_left = left_bound
    for child_id, num_leaves in child_leaves:
        proportion = num_leaves / total_leaves
        child_width = (right_bound - left_bound) * proportion
        child_right = current_left + child_width
        assign_x_positions(child_id, current_left, child_right)
        current_left = child_right

    # Parent is centered over its children
    child_x_values = [x_pos[c] for c in children[node_id]]
    x_pos[node_id] = (min(child_x_values) + max(child_x_values)) / 2


# Assign x positions starting from root
assign_x_positions(0, 0, 1)

# Assign y positions based on level (root at top)
max_level = max(node["level"] for node in nodes)
for node in nodes:
    y_pos[node["id"]] = 1 - (node["level"] / max_level)

# Level colors - different colors for each organizational level
level_colors = ["#306998", "#FFD43B", "#2CA02C", "#E64A19"]
level_names = ["Executive", "VP", "Manager", "Staff"]

# Create edges dataframe
edge_data = []
for parent, child in edges:
    x0, y0 = x_pos[parent], y_pos[parent]
    x1, y1 = x_pos[child], y_pos[child]
    edge_data.append({"x": x0, "y": y0, "xend": x1, "yend": y1})

df_edges = pd.DataFrame(edge_data)

# Create nodes dataframe
node_data = []
for node in nodes:
    nid = node["id"]
    level = node["level"]
    # Size nodes by level (executives larger)
    size = 18 - level * 3
    node_data.append(
        {
            "x": x_pos[nid],
            "y": y_pos[nid],
            "label": node["label"],
            "level_name": level_names[level],
            "size": size,
            "label_y": y_pos[nid] + 0.035,
        }
    )

df_nodes = pd.DataFrame(node_data)

# Build the plot
plot = (
    ggplot()
    # Draw edges (straight lines connecting parent to child)
    + geom_segment(aes(x="x", y="y", xend="xend", yend="yend"), data=df_edges, color="#666666", size=1.5, alpha=0.6)
    # Draw nodes colored by level
    + geom_point(aes(x="x", y="y", color="level_name", size="size"), data=df_nodes, stroke=2, alpha=0.95)
    # Add node labels
    + geom_text(aes(x="x", y="label_y", label="label"), data=df_nodes, size=8, color="#222222", fontface="bold")
    + scale_color_manual(values=level_colors, name="Level")
    + scale_size_identity()
    + scale_x_continuous(limits=(-0.05, 1.05))
    + scale_y_continuous(limits=(-0.08, 1.12))
    + labs(title="Tech Company Org Chart · network-hierarchical · letsplot · pyplots.ai")
    + ggsize(1600, 900)
    + theme(
        plot_title=element_text(size=26, face="bold"),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        legend_text=element_text(size=14),
        legend_title=element_text(size=16, face="bold"),
        legend_position="right",
    )
)

# Save as PNG (scale 3x to get 4800 x 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
