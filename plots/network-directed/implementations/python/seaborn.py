""" pyplots.ai
network-directed: Directed Network Graph
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set seaborn style
sns.set_theme(style="white")

np.random.seed(42)

# Software module dependencies data with improved circular-hierarchical layout
# Positions organized in concentric layers for better visual balance
modules = {
    "app": {"group": "core", "pos": (0.5, 0.88)},
    "config": {"group": "core", "pos": (0.18, 0.70)},
    "api": {"group": "services", "pos": (0.50, 0.68)},
    "auth": {"group": "services", "pos": (0.82, 0.70)},
    "db": {"group": "data", "pos": (0.28, 0.45)},
    "cache": {"group": "data", "pos": (0.72, 0.45)},
    "log": {"group": "utils", "pos": (0.15, 0.22)},
    "valid": {"group": "utils", "pos": (0.50, 0.22)},
    "router": {"group": "services", "pos": (0.85, 0.22)},
    "model": {"group": "data", "pos": (0.32, 0.05)},
    "mware": {"group": "services", "pos": (0.68, 0.05)},
}

# Directed edges with weights (source → target, weight)
# Weight represents dependency strength/frequency
edges = [
    ("app", "config", 3),
    ("app", "db", 5),
    ("app", "api", 5),
    ("app", "auth", 4),
    ("api", "valid", 4),
    ("api", "router", 3),
    ("api", "log", 2),
    ("auth", "cache", 4),
    ("auth", "db", 3),
    ("auth", "log", 2),
    ("db", "config", 3),
    ("db", "log", 1),
    ("cache", "config", 2),
    ("router", "valid", 3),
    ("router", "mware", 2),
    ("model", "db", 4),
    ("model", "valid", 3),
    ("mware", "auth", 3),
    ("mware", "log", 1),
]

# Color palette using seaborn
groups = ["core", "data", "services", "utils"]
palette = sns.color_palette(["#306998", "#FFD43B", "#4CAF50", "#E57373"], n_colors=4)
group_colors = dict(zip(groups, palette, strict=True))

# Prepare node data as DataFrame for seaborn
node_data = []
for name, data in modules.items():
    node_data.append({"name": name, "x": data["pos"][0], "y": data["pos"][1], "group": data["group"]})
nodes_df = pd.DataFrame(node_data)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw all edges with directed arrows - thickness based on weight
for source, target, weight in edges:
    start = modules[source]["pos"]
    end = modules[target]["pos"]

    # Calculate direction for shortening arrows
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = np.sqrt(dx**2 + dy**2)
    dx_norm = dx / length if length > 0 else 0
    dy_norm = dy / length if length > 0 else 0

    # Shorten to avoid overlapping nodes
    shrink = 0.055
    start_adj = (start[0] + dx_norm * shrink, start[1] + dy_norm * shrink)
    end_adj = (end[0] - dx_norm * shrink, end[1] - dy_norm * shrink)

    # Line width based on edge weight (1-5 scale to 1.5-4.0 linewidth)
    line_width = 1.0 + weight * 0.6

    # Draw arrow using FancyArrowPatch with weight-based thickness
    arrow = mpatches.FancyArrowPatch(
        start_adj,
        end_adj,
        connectionstyle="arc3,rad=0.1",
        arrowstyle="->,head_length=8,head_width=5",
        color="#555555",
        alpha=0.5 + weight * 0.08,
        linewidth=line_width,
        zorder=1,
    )
    ax.add_patch(arrow)

# Draw nodes using seaborn's scatterplot
sns.scatterplot(
    data=nodes_df,
    x="x",
    y="y",
    hue="group",
    palette=group_colors,
    s=3000,
    edgecolor="white",
    linewidth=3,
    legend=False,
    ax=ax,
    zorder=2,
)

# Add node labels with larger font size (14-16pt per feedback)
for name, data in modules.items():
    ax.text(
        data["pos"][0],
        data["pos"][1],
        name,
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="white" if data["group"] != "data" else "#333333",
        zorder=3,
    )

# Create legend with edge weight indicator
legend_handles = [
    plt.scatter([], [], c=[group_colors[g]], s=400, label=g.capitalize(), edgecolors="white", linewidths=2)
    for g in groups
]
# Add edge weight legend entries
legend_handles.append(plt.Line2D([0], [0], color="#555555", linewidth=1.6, label="Weak (1)", alpha=0.6))
legend_handles.append(plt.Line2D([0], [0], color="#555555", linewidth=4.0, label="Strong (5)", alpha=0.9))

ax.legend(
    handles=legend_handles,
    loc="upper left",
    fontsize=14,
    title="Module Type / Edge Weight",
    title_fontsize=16,
    framealpha=0.95,
    markerscale=1.0,
    borderpad=1,
)

# Styling
ax.set_title("network-directed · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.08, 1.02)
ax.axis("off")
ax.set_facecolor("#fafafa")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
