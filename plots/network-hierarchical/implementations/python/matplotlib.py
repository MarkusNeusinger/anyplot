""" pyplots.ai
network-hierarchical: Hierarchical Network Graph with Tree Layout
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data: Software Module Hierarchy (24 nodes, 4 levels)
np.random.seed(42)

# Build hierarchical structure with explicit ordering
# Format: (label, level, parent_id)
nodes = [
    # Level 0 - Root
    ("app", "App", 0, None),
    # Level 1 - Core modules (4 nodes)
    ("core", "Core", 1, "app"),
    ("ui", "UI", 1, "app"),
    ("data", "Data", 1, "app"),
    ("utils", "Utils", 1, "app"),
    # Level 2 - Sub-modules (8 nodes - 2 per parent)
    ("auth", "Auth", 2, "core"),
    ("config", "Config", 2, "core"),
    ("widgets", "Widget", 2, "ui"),
    ("themes", "Theme", 2, "ui"),
    ("models", "Models", 2, "data"),
    ("store", "Store", 2, "data"),
    ("logger", "Logger", 2, "utils"),
    ("helpers", "Helper", 2, "utils"),
    # Level 3 - Leaf modules (11 nodes)
    ("login", "Login", 3, "auth"),
    ("session", "Sess", 3, "auth"),
    ("buttons", "Btns", 3, "widgets"),
    ("forms", "Forms", 3, "widgets"),
    ("grid", "Grid", 3, "themes"),
    ("user", "User", 3, "models"),
    ("product", "Prod", 3, "models"),
    ("cache", "Cache", 3, "store"),
    ("db", "DB", 3, "store"),
    ("rest", "REST", 3, "logger"),
    ("format", "Fmt", 3, "helpers"),
]

# Create lookup dictionaries
hierarchy = {n[0]: (n[1], n[2], n[3]) for n in nodes}

# Group nodes by level maintaining order
levels = {0: [], 1: [], 2: [], 3: []}
for node_id, _label, level, _parent in nodes:
    levels[level].append(node_id)


# Calculate positions using a breadth-first approach
# First, calculate how many leaf descendants each node has
def count_descendants(node_id):
    """Count total leaf descendants for proper spacing."""
    children = [n[0] for n in nodes if n[3] == node_id]
    if not children:
        return 1
    return sum(count_descendants(c) for c in children)


# Calculate positions based on leaf counts for proper spacing
positions = {}
y_positions = {0: 8.5, 1: 6.0, 2: 3.5, 3: 1.0}

# Position level 3 (leaves) first with even spacing
level3_nodes = levels[3]
n_leaves = len(level3_nodes)
x_positions_l3 = np.linspace(1, 15, n_leaves)
for i, node_id in enumerate(level3_nodes):
    positions[node_id] = (x_positions_l3[i], y_positions[3])

# Position level 2 - center each parent over its children
for node_id in levels[2]:
    children = [n[0] for n in nodes if n[3] == node_id]
    if children:
        child_xs = [positions[c][0] for c in children]
        positions[node_id] = (np.mean(child_xs), y_positions[2])
    else:
        # No children - position based on order in level
        idx = levels[2].index(node_id)
        positions[node_id] = (2 + idx * 1.6, y_positions[2])

# Position level 1 - center each parent over its children
for node_id in levels[1]:
    children = [n[0] for n in nodes if n[3] == node_id]
    if children:
        child_xs = [positions[c][0] for c in children]
        positions[node_id] = (np.mean(child_xs), y_positions[1])

# Position level 0 - center over children
for node_id in levels[0]:
    children = [n[0] for n in nodes if n[3] == node_id]
    if children:
        child_xs = [positions[c][0] for c in children]
        positions[node_id] = (np.mean(child_xs), y_positions[0])

# Define colors for each level
level_colors = {
    0: "#306998",  # Python Blue - Root
    1: "#FFD43B",  # Python Yellow - Level 1
    2: "#4B8BBE",  # Light Blue - Level 2
    3: "#7A7A7A",  # Gray - Level 3 (Leaves)
}
level_names = ["Root Module", "Core Modules", "Sub-modules", "Leaf Modules"]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw edges (parent-child connections)
for node_id, _label, _level, parent_id in nodes:
    if parent_id is not None:
        x1, y1 = positions[parent_id]
        x2, y2 = positions[node_id]
        ax.plot([x1, x2], [y1, y2], color="#AAAAAA", linewidth=2.5, alpha=0.6, zorder=1)

# Draw nodes by level
for level in [3, 2, 1, 0]:
    level_node_ids = levels[level]
    for node_id in level_node_ids:
        x, y = positions[node_id]
        label = hierarchy[node_id][0]
        color = level_colors[level]

        # Node size based on level
        node_size = {0: 3200, 1: 2400, 2: 1800, 3: 1300}[level]

        ax.scatter(x, y, s=node_size, c=color, edgecolors="white", linewidths=2.5, zorder=10 + level, alpha=0.95)

        # Add label inside node
        font_size = {0: 16, 1: 14, 2: 12, 3: 10}[level]
        text_color = "white" if level in [0, 2] else "black"

        ax.annotate(
            label,
            (x, y),
            ha="center",
            va="center",
            fontsize=font_size,
            fontweight="bold",
            color=text_color,
            zorder=20 + level,
        )

# Create legend
legend_handles = [mpatches.Patch(color=level_colors[i], label=level_names[i]) for i in range(4)]
ax.legend(handles=legend_handles, loc="upper left", fontsize=14, framealpha=0.9, edgecolor="gray")

# Styling
ax.set_title(
    "Software Module Hierarchy · network-hierarchical · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20
)
ax.set_xlim(-0.5, 16.5)
ax.set_ylim(-0.5, 10)
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
