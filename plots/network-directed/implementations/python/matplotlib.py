""" pyplots.ai
network-directed: Directed Network Graph
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch


# Data: Software package dependencies (arrows show import direction)
np.random.seed(42)

# Define modules with groups (core, utils, api, tests)
# Positions optimized for 16:9 aspect ratio with better spread
nodes = {
    "main": {"group": "core", "pos": (0.45, 0.88)},
    "config": {"group": "core", "pos": (0.18, 0.68)},
    "database": {"group": "core", "pos": (0.45, 0.55)},
    "auth": {"group": "api", "pos": (0.72, 0.73)},
    "routes": {"group": "api", "pos": (0.88, 0.52)},
    "handlers": {"group": "api", "pos": (0.68, 0.32)},
    "validators": {"group": "utils", "pos": (0.32, 0.38)},
    "helpers": {"group": "utils", "pos": (0.48, 0.15)},
    "logger": {"group": "utils", "pos": (0.12, 0.38)},
    "cache": {"group": "utils", "pos": (0.05, 0.58)},
    "test_auth": {"group": "tests", "pos": (0.92, 0.88)},
    "test_routes": {"group": "tests", "pos": (0.95, 0.32)},
    "test_db": {"group": "tests", "pos": (0.25, 0.12)},
}

# Define dependencies (arrow from source to target means source imports target)
edges = [
    ("main", "config"),
    ("main", "database"),
    ("main", "routes"),
    ("main", "logger"),
    ("config", "validators"),
    ("database", "logger"),
    ("database", "config"),
    ("auth", "database"),
    ("auth", "validators"),
    ("auth", "logger"),
    ("routes", "auth"),
    ("routes", "handlers"),
    ("routes", "validators"),
    ("handlers", "database"),
    ("handlers", "helpers"),
    ("handlers", "logger"),
    ("validators", "helpers"),
    ("cache", "logger"),
    ("cache", "config"),
    ("test_auth", "auth"),
    ("test_routes", "routes"),
    ("test_db", "database"),
]

# Group colors (colorblind-safe palette)
group_colors = {
    "core": "#306998",  # Python Blue
    "api": "#FFD43B",  # Python Yellow
    "utils": "#4DAF4A",  # Green
    "tests": "#984EA3",  # Purple
}

# Create plot (16:9 for directed graph)
fig, ax = plt.subplots(figsize=(16, 9))

# Node radius for arrow endpoint calculations
node_radius = 0.055

# Draw edges with arrows
for source, target in edges:
    pos1 = nodes[source]["pos"]
    pos2 = nodes[target]["pos"]

    # Calculate edge start/end points outside node circles
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    dist = np.sqrt(dx**2 + dy**2)
    dx_norm, dy_norm = dx / dist, dy / dist
    start = (pos1[0] + dx_norm * node_radius, pos1[1] + dy_norm * node_radius)
    end = (pos2[0] - dx_norm * node_radius * 1.6, pos2[1] - dy_norm * node_radius * 1.6)

    # Create curved arrow
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=25,
        color="#555555",
        linewidth=2.5,
        alpha=0.65,
        connectionstyle="arc3,rad=0.12",
    )
    ax.add_patch(arrow)

# Draw nodes
for name, props in nodes.items():
    pos = props["pos"]
    color = group_colors[props["group"]]

    # Draw node circle
    circle = Circle(pos, radius=node_radius, facecolor=color, edgecolor="#333333", linewidth=2.5, alpha=0.95, zorder=10)
    ax.add_patch(circle)

    # Draw label
    ax.text(pos[0], pos[1], name, ha="center", va="center", fontsize=13, fontweight="bold", color="#222222", zorder=11)

# Create legend
legend_handles = [
    mpatches.Patch(color=color, label=group.capitalize(), alpha=0.95) for group, color in group_colors.items()
]
ax.legend(
    handles=legend_handles, loc="upper left", fontsize=16, framealpha=0.95, title="Module Type", title_fontsize=18
)

# Styling
ax.set_title("network-directed · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(0.0, 1.0)
ax.set_aspect("equal")
ax.axis("off")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
