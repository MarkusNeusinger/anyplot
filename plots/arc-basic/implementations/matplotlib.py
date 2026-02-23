""" pyplots.ai
arc-basic: Basic Arc Diagram
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-23
"""

import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import numpy as np


# Data: Character interactions in a story chapter
nodes = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Iris", "Jack"]
n_nodes = len(nodes)

# Edges: (source_index, target_index, weight)
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

weights = [w for _, _, w in edges]
weight_min, weight_max = min(weights), max(weights)

# Weighted node degrees for size variation (data storytelling)
node_degrees = [0] * n_nodes
for s, e, w in edges:
    node_degrees[s] += w
    node_degrees[e] += w

# Truncated Blues colormap — avoids near-white so weight-1 arcs stay clearly visible
blues_raw = plt.cm.Blues(np.linspace(0.35, 0.95, 256))
arc_cmap = mcolors.LinearSegmentedColormap.from_list("TruncBlues", blues_raw)
norm = mcolors.Normalize(vmin=weight_min, vmax=weight_max)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

x_positions = np.linspace(0.06, 0.90, n_nodes)
y_baseline = 0.08

# Arcs via PathPatch with cubic Bézier curves (distinctive matplotlib feature)
for start, end, weight in sorted(edges, key=lambda e: e[2]):
    x_start = x_positions[start]
    x_end = x_positions[end]
    distance = abs(end - start)
    peak = 0.065 * distance

    path = mpath.Path(
        [
            (x_start, y_baseline),
            (x_start, y_baseline + peak * 1.35),
            (x_end, y_baseline + peak * 1.35),
            (x_end, y_baseline),
        ],
        [mpath.Path.MOVETO, mpath.Path.CURVE4, mpath.Path.CURVE4, mpath.Path.CURVE4],
    )

    patch = mpatches.PathPatch(
        path,
        facecolor="none",
        edgecolor=arc_cmap(norm(weight)),
        linewidth=1.5 + weight * 1.8,
        alpha=0.8,
        capstyle="round",
    )
    ax.add_patch(patch)

# Node sizes proportional to weighted degree (reveals hub characters)
max_degree = max(node_degrees)
node_sizes = [300 + 350 * (d / max_degree) for d in node_degrees]

# Highlight protagonist Alice with distinct accent color
node_colors = ["#FF6B35" if i == 0 else "#FFD43B" for i in range(n_nodes)]
node_edge_colors = ["#B8441A" if i == 0 else "#306998" for i in range(n_nodes)]

ax.scatter(
    x_positions,
    [y_baseline] * n_nodes,
    s=node_sizes,
    c=node_colors,
    edgecolors=node_edge_colors,
    linewidths=2.5,
    zorder=5,
)

# Node labels with typographic hierarchy
for i, (x, name) in enumerate(zip(x_positions, nodes, strict=True)):
    ax.text(
        x,
        y_baseline - 0.04,
        name,
        ha="center",
        va="top",
        fontsize=16,
        fontweight="heavy" if i == 0 else "bold",
        color="#306998",
    )

# Colorbar for connection strength
sm = plt.cm.ScalarMappable(cmap=arc_cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.4, aspect=15, pad=0.02)
cbar.set_label("Connection Strength", fontsize=16)
cbar.set_ticks([1, 2, 3])
cbar.ax.tick_params(labelsize=16)

# Subtle baseline
ax.plot(
    [x_positions[0] - 0.02, x_positions[-1] + 0.02],
    [y_baseline, y_baseline],
    color="#306998",
    linewidth=0.8,
    alpha=0.2,
    zorder=1,
)

# Layout
ax.set_xlim(-0.02, 0.98)
ax.set_ylim(-0.06, 0.68)
ax.axis("off")

# Title with narrative subtitle
ax.set_title(
    "Character Interactions \u00b7 arc-basic \u00b7 matplotlib \u00b7 pyplots.ai",
    fontsize=24,
    fontweight="medium",
    pad=36,
)

ax.text(
    0.5,
    1.01,
    "Node size reflects connection activity \u00b7 Alice (orange) is the central character",
    ha="center",
    va="bottom",
    fontsize=13,
    color="#888888",
    fontstyle="italic",
    transform=ax.transAxes,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
