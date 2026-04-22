""" pyplots.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_size_identity,
    theme,
    xlim,
    ylim,
)


# Data: Software company organizational hierarchy (22 employees, 4 levels)
# Reduced from 30 to prevent label crowding at bottom level
nodes = [
    # Level 0 - CEO
    {"id": 0, "label": "CEO", "level": 0},
    # Level 1 - VPs (3 people)
    {"id": 1, "label": "VP Engineering", "level": 1},
    {"id": 2, "label": "VP Product", "level": 1},
    {"id": 3, "label": "VP Operations", "level": 1},
    # Level 2 - Directors/Managers (6 people)
    {"id": 4, "label": "Frontend Dir", "level": 2},
    {"id": 5, "label": "Backend Dir", "level": 2},
    {"id": 6, "label": "PM Lead", "level": 2},
    {"id": 7, "label": "UX Lead", "level": 2},
    {"id": 8, "label": "IT Manager", "level": 2},
    {"id": 9, "label": "HR Manager", "level": 2},
    # Level 3 - Team Members (12 people)
    {"id": 10, "label": "FE Dev 1", "level": 3},
    {"id": 11, "label": "FE Dev 2", "level": 3},
    {"id": 12, "label": "BE Dev 1", "level": 3},
    {"id": 13, "label": "BE Dev 2", "level": 3},
    {"id": 14, "label": "PM 1", "level": 3},
    {"id": 15, "label": "Designer", "level": 3},
    {"id": 16, "label": "UX Rsrch", "level": 3},
    {"id": 17, "label": "SysAdmin", "level": 3},
    {"id": 18, "label": "DevOps", "level": 3},
    {"id": 19, "label": "Recruiter", "level": 3},
    {"id": 20, "label": "Payroll", "level": 3},
    {"id": 21, "label": "Benefits", "level": 3},
]

edges = [
    # CEO to VPs
    (0, 1),
    (0, 2),
    (0, 3),
    # VP Engineering to Directors
    (1, 4),
    (1, 5),
    # VP Product to Leads
    (2, 6),
    (2, 7),
    # VP Operations to Managers
    (3, 8),
    (3, 9),
    # Directors to Team Members
    (4, 10),
    (4, 11),
    (5, 12),
    (5, 13),
    (6, 14),
    (7, 15),
    (7, 16),
    (8, 17),
    (8, 18),
    (9, 19),
    (9, 20),
    (9, 21),
]

# Compute hierarchical layout positions
# Group nodes by level
levels = {}
for node in nodes:
    lvl = node["level"]
    if lvl not in levels:
        levels[lvl] = []
    levels[lvl].append(node)

# Calculate positions: levels spread vertically, nodes at each level spread horizontally
positions = {}
y_spacing = 0.22  # Vertical spacing between levels
for lvl in sorted(levels.keys()):
    nodes_at_level = levels[lvl]
    n = len(nodes_at_level)
    # Spread nodes horizontally with even distribution
    if n > 1:
        x_positions = [0.05 + i * (0.90 / (n - 1)) for i in range(n)]
    else:
        x_positions = [0.5]
    y_pos = 0.90 - lvl * y_spacing  # Root at top
    for i, node in enumerate(nodes_at_level):
        positions[node["id"]] = (x_positions[i], y_pos)

# Define colors by level - Python Blue for CEO, Yellow for VPs
level_colors = {
    "Level 0: CEO": "#306998",
    "Level 1: VPs": "#FFD43B",
    "Level 2: Directors": "#4ECDC4",
    "Level 3: Team": "#FF6B6B",
}
level_names = {0: "Level 0: CEO", 1: "Level 1: VPs", 2: "Level 2: Directors", 3: "Level 3: Team"}

# Node sizes by level (higher = larger)
size_map = {0: 16, 1: 12, 2: 9, 3: 6}

# Create node dataframe
node_df = pd.DataFrame(
    {
        "x": [positions[node["id"]][0] for node in nodes],
        "y": [positions[node["id"]][1] for node in nodes],
        "label": [node["label"] for node in nodes],
        "level": [level_names[node["level"]] for node in nodes],
        "size": [size_map[node["level"]] for node in nodes],
    }
)

# Create edge dataframe
edge_data = []
for parent, child in edges:
    edge_data.append(
        {"x": positions[parent][0], "y": positions[parent][1], "xend": positions[child][0], "yend": positions[child][1]}
    )
edge_df = pd.DataFrame(edge_data)

# Create the plot
plot = (
    ggplot()
    # Draw edges first (underneath nodes)
    + geom_segment(
        data=edge_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), color="#555555", size=1.2, alpha=0.7
    )
    # Draw nodes colored by level
    + geom_point(data=node_df, mapping=aes(x="x", y="y", color="level", size="size"), alpha=0.95, stroke=0.5)
    # Add node labels with offset above nodes
    + geom_text(
        data=node_df, mapping=aes(x="x", y="y", label="label"), size=8, va="bottom", nudge_y=0.025, color="#222222"
    )
    + scale_color_manual(values=level_colors)
    + scale_size_identity()
    + labs(title="network-hierarchical · plotnine · pyplots.ai", color="Hierarchy Level")
    + xlim(-0.02, 1.02)
    + ylim(0.18, 1.0)
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center"),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="bottom",
        legend_box_margin=10,
        legend_margin=5,
        legend_background=element_rect(fill="white", alpha=0.95),
        legend_key=element_rect(fill="white"),
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
