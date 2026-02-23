""" pyplots.ai
arc-basic: Basic Arc Diagram
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 85/100 | Updated: 2026-02-23
"""

import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


# Data: Character interactions in a story chapter
nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]
n_nodes = len(nodes)

# Edges: pairs of connected nodes with weights (start, end, weight)
edges = [
    (0, 1, 3),  # Alice-Bob (strong connection)
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

weights = [w for _, _, w in edges]
weight_min, weight_max = min(weights), max(weights)

# Colormap: weight mapped to blue palette (truncated to avoid near-white)
norm = mcolors.Normalize(vmin=weight_min - 0.8, vmax=weight_max + 0.3)
cmap = cm.Blues

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Node positions along x-axis
x_positions = np.linspace(0.05, 0.92, n_nodes)
y_baseline = 0.10

# Draw arcs (lighter weights first so strong connections render on top)
for start, end, weight in sorted(edges, key=lambda e: e[2]):
    x_start = x_positions[start]
    x_end = x_positions[end]

    # Arc height proportional to distance between nodes
    distance = abs(end - start)
    height = 0.06 * distance

    x_center = (x_start + x_end) / 2
    arc_width = abs(x_end - x_start)

    # Thickness and color both encode weight
    linewidth = 1.5 + weight * 1.5
    color = cmap(norm(weight))

    arc = mpatches.Arc(
        (x_center, y_baseline),
        width=arc_width,
        height=height * 2,
        angle=0,
        theta1=0,
        theta2=180,
        color=color,
        linewidth=linewidth,
        alpha=0.75,
    )
    ax.add_patch(arc)

# Draw nodes
ax.scatter(x_positions, [y_baseline] * n_nodes, s=500, c="#FFD43B", edgecolors="#306998", linewidths=2.5, zorder=5)

# Node labels
for x, name in zip(x_positions, nodes, strict=True):
    ax.text(x, y_baseline - 0.045, name, ha="center", va="top", fontsize=16, fontweight="bold", color="#306998")

# Weight colorbar (distinctive matplotlib feature)
tick_norm = mcolors.Normalize(vmin=weight_min, vmax=weight_max)
sm = cm.ScalarMappable(cmap=cmap, norm=tick_norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.45, aspect=15, pad=0.02)
cbar.set_label("Connection Strength", fontsize=16)
cbar.set_ticks([1, 2, 3])
cbar.ax.tick_params(labelsize=14)

# Baseline indicator (thin horizontal line for visual grounding)
ax.plot(
    [x_positions[0] - 0.02, x_positions[-1] + 0.02],
    [y_baseline, y_baseline],
    color="#306998",
    linewidth=0.8,
    alpha=0.25,
    zorder=1,
)

# Styling
ax.set_xlim(-0.02, 0.98)
ax.set_ylim(-0.07, 0.68)
ax.axis("off")

ax.set_title(
    "Character Interactions \u00b7 arc-basic \u00b7 matplotlib \u00b7 pyplots.ai",
    fontsize=24,
    fontweight="medium",
    pad=20,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
