"""pyplots.ai
arc-basic: Basic Arc Diagram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: /100 | Updated: 2026-02-23
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Character interactions in a story (12 characters for readability)
nodes = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack", "Kate", "Leo"]
n_nodes = len(nodes)

# Edges with weights (character interaction strength)
edges = [
    (0, 1, 5),  # Alice - Bob (close friends)
    (0, 3, 2),  # Alice - Dave
    (1, 2, 4),  # Bob - Carol
    (1, 4, 3),  # Bob - Eve
    (2, 5, 2),  # Carol - Frank
    (3, 4, 5),  # Dave - Eve (close)
    (3, 6, 3),  # Dave - Grace
    (4, 7, 4),  # Eve - Henry
    (5, 6, 2),  # Frank - Grace
    (0, 11, 1),  # Alice - Leo (distant, long arc)
    (2, 6, 3),  # Carol - Grace
    (1, 5, 2),  # Bob - Frank
    (7, 8, 4),  # Henry - Ivy
    (8, 9, 3),  # Ivy - Jack
    (9, 10, 5),  # Jack - Kate (close)
    (10, 11, 2),  # Kate - Leo
    (6, 9, 2),  # Grace - Jack
    (5, 10, 1),  # Frank - Kate (distant)
]

# Node positions along x-axis
x_positions = np.arange(n_nodes)

# Color arcs by weight using a seaborn sequential palette
weights = [w for _, _, w in edges]
arc_palette = sns.color_palette("flare", as_cmap=True)
weight_min, weight_max = min(weights), max(weights)
norm = plt.Normalize(vmin=weight_min, vmax=weight_max)

# Plot
sns.set_theme(style="white", context="talk", font_scale=1.1)
fig, ax = plt.subplots(figsize=(16, 9))
ax.grid(False)

# Plot nodes using seaborn scatterplot
node_data = pd.DataFrame({"x": x_positions, "y": np.zeros(n_nodes), "node": nodes})
sns.scatterplot(data=node_data, x="x", y="y", s=600, color="#306998", zorder=5, ax=ax, legend=False)

# Draw arcs for each edge
for start, end, weight in edges:
    x1, x2 = x_positions[start], x_positions[end]
    distance = abs(x2 - x1)
    height = distance * 0.4
    linewidth = weight * 0.9 + 0.5
    center_x = (x1 + x2) / 2
    width = abs(x2 - x1)

    arc_color = arc_palette(norm(weight))
    arc = patches.Arc(
        (center_x, 0),
        width,
        height * 2,
        angle=0,
        theta1=0,
        theta2=180,
        color=arc_color,
        linewidth=linewidth,
        alpha=0.65,
        zorder=2,
    )
    ax.add_patch(arc)

# Node labels below the axis
for i, name in enumerate(nodes):
    ax.text(x_positions[i], -0.18, name, ha="center", va="top", fontsize=16, fontweight="medium", color="#306998")

# Style
ax.set_xlim(-0.8, n_nodes - 0.2)
ax.set_ylim(-1.0, 5.2)
ax.set_title("arc-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, pad=20)
ax.set_xlabel("")
ax.set_ylabel("")
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_xticks([])
ax.set_yticks([])

# Subtle horizontal baseline
ax.axhline(y=0, color="#306998", linewidth=2, alpha=0.3, zorder=1)

# Colorbar for interaction strength
sm = plt.cm.ScalarMappable(cmap=arc_palette, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.35, aspect=15, pad=0.015)
cbar.set_label("Interaction Strength", fontsize=16)
cbar.set_ticks([1, 2, 3, 4, 5])
cbar.ax.tick_params(labelsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
