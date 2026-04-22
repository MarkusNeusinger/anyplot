""" pyplots.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-08
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set seaborn style for enhanced aesthetics
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

np.random.seed(42)

# Data: Software project team hierarchy (24 employees, 4 levels)
nodes = [
    # Level 0 - CEO
    {"id": 0, "label": "CEO", "level": 0},
    # Level 1 - VPs
    {"id": 1, "label": "VP Engineering", "level": 1},
    {"id": 2, "label": "VP Product", "level": 1},
    {"id": 3, "label": "VP Operations", "level": 1},
    # Level 2 - Directors/Managers
    {"id": 4, "label": "Frontend Dir.", "level": 2},
    {"id": 5, "label": "Backend Dir.", "level": 2},
    {"id": 6, "label": "PM Lead", "level": 2},
    {"id": 7, "label": "UX Lead", "level": 2},
    {"id": 8, "label": "IT Manager", "level": 2},
    {"id": 9, "label": "HR Manager", "level": 2},
    # Level 3 - Team Members
    {"id": 10, "label": "FE Dev 1", "level": 3},
    {"id": 11, "label": "FE Dev 2", "level": 3},
    {"id": 12, "label": "BE Dev 1", "level": 3},
    {"id": 13, "label": "BE Dev 2", "level": 3},
    {"id": 14, "label": "BE Dev 3", "level": 3},
    {"id": 15, "label": "PM 1", "level": 3},
    {"id": 16, "label": "PM 2", "level": 3},
    {"id": 17, "label": "Designer 1", "level": 3},
    {"id": 18, "label": "Designer 2", "level": 3},
    {"id": 19, "label": "IT Support 1", "level": 3},
    {"id": 20, "label": "IT Support 2", "level": 3},
    {"id": 21, "label": "HR Spec 1", "level": 3},
    {"id": 22, "label": "HR Spec 2", "level": 3},
    {"id": 23, "label": "Recruiter", "level": 3},
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
    (5, 14),
    (6, 15),
    (6, 16),
    (7, 17),
    (7, 18),
    (8, 19),
    (8, 20),
    (9, 21),
    (9, 22),
    (9, 23),
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
y_spacing = 2.0
for lvl in sorted(levels.keys()):
    nodes_at_level = levels[lvl]
    n = len(nodes_at_level)
    spread = max(n * 1.4, 6)
    x_positions = np.linspace(-spread / 2, spread / 2, n)
    y_pos = -lvl * y_spacing
    for i, node in enumerate(nodes_at_level):
        positions[node["id"]] = (x_positions[i], y_pos)

# Prepare data for plotting
node_x = [positions[n["id"]][0] for n in nodes]
node_y = [positions[n["id"]][1] for n in nodes]
node_labels = [n["label"] for n in nodes]
node_levels = [n["level"] for n in nodes]

# Color palette by level using seaborn - Python Blue and Yellow as primary
level_colors = ["#306998", "#FFD43B", "#4B8BBE", "#8BC34A"]
level_names = ["CEO", "VPs", "Directors", "Team Members"]

# Node sizes based on level
size_map = {0: 800, 1: 600, 2: 450, 3: 350}
node_sizes = [size_map[lvl] for lvl in node_levels]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw edges first (underneath nodes)
for parent, child in edges:
    x0, y0 = positions[parent]
    x1, y1 = positions[child]
    ax.plot([x0, x1], [y0, y1], color="#555555", linewidth=2.5, alpha=0.7, zorder=1)

# Draw nodes by level using seaborn scatterplot for styling and legend
for lvl in range(4):
    lvl_indices = [i for i, n in enumerate(nodes) if n["level"] == lvl]
    lvl_x = [node_x[i] for i in lvl_indices]
    lvl_y = [node_y[i] for i in lvl_indices]
    lvl_sizes = [node_sizes[i] for i in lvl_indices]

    sns.scatterplot(
        x=lvl_x,
        y=lvl_y,
        s=lvl_sizes,
        color=level_colors[lvl],
        edgecolor="#333333",
        linewidth=2,
        label=f"Level {lvl}: {level_names[lvl]}",
        ax=ax,
        zorder=2,
    )

# Add node labels
for node in nodes:
    x, y = positions[node["id"]]
    lvl = node["level"]
    fontsize = 12 if lvl <= 1 else 10 if lvl == 2 else 9
    fontweight = "bold" if lvl == 0 else "normal"
    ax.annotate(
        node["label"],
        (x, y),
        textcoords="offset points",
        xytext=(0, -22),
        ha="center",
        va="top",
        fontsize=fontsize,
        fontweight=fontweight,
        color="#222222",
    )

# Style the plot
ax.set_title("network-hierarchical · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)

# Hide axis ticks but add descriptive labels
ax.set_xlabel("Organization Width", fontsize=20)
ax.set_ylabel("Hierarchy Level (Top to Bottom)", fontsize=20)
ax.set_xticks([])
ax.set_yticks([])

# Set axis limits with padding
x_padding = 1.5
y_padding = 1.0
ax.set_xlim(min(node_x) - x_padding, max(node_x) + x_padding)
ax.set_ylim(min(node_y) - y_padding, max(node_y) + y_padding)

# Configure legend
ax.legend(title="Hierarchy", title_fontsize=16, fontsize=14, loc="upper right", framealpha=0.9, markerscale=0.8)

# Remove grid for cleaner network visualization
ax.grid(False)
ax.set_facecolor("#f8f9fa")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
