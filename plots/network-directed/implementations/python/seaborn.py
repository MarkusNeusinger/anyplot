""" anyplot.ai
network-directed: Directed Network Graph
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-14
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for node groups
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

np.random.seed(42)

sns.set_theme(
    style="white",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Software module dependencies with hierarchical layout
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

# Directed edges with weights
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

# Map groups to Okabe-Ito palette
groups = ["core", "data", "services", "utils"]
group_colors = {"core": IMPRINT[0], "data": IMPRINT[1], "services": IMPRINT[2], "utils": IMPRINT[3]}

# Prepare node data
node_data = []
for name, data in modules.items():
    node_data.append({"name": name, "x": data["pos"][0], "y": data["pos"][1], "group": data["group"]})
nodes_df = pd.DataFrame(node_data)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw edges with directed arrows
for source, target, weight in edges:
    start = modules[source]["pos"]
    end = modules[target]["pos"]

    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = np.sqrt(dx**2 + dy**2)
    dx_norm = dx / length if length > 0 else 0
    dy_norm = dy / length if length > 0 else 1

    # Shorten arrows to avoid overlapping nodes
    shrink = 0.055
    start_adj = (start[0] + dx_norm * shrink, start[1] + dy_norm * shrink)
    end_adj = (end[0] - dx_norm * shrink, end[1] - dy_norm * shrink)

    line_width = 1.0 + weight * 0.6

    arrow = mpatches.FancyArrowPatch(
        start_adj,
        end_adj,
        connectionstyle="arc3,rad=0.1",
        arrowstyle="->,head_length=8,head_width=5",
        color=INK_SOFT,
        alpha=0.5 + weight * 0.08,
        linewidth=line_width,
        zorder=1,
    )
    ax.add_patch(arrow)

# Draw nodes
palette_list = [group_colors[g] for g in nodes_df["group"]]
sns.scatterplot(
    data=nodes_df,
    x="x",
    y="y",
    hue="group",
    palette=group_colors,
    s=3000,
    edgecolor=PAGE_BG,
    linewidth=3,
    legend=False,
    ax=ax,
    zorder=2,
)

# Add node labels
for name, data in modules.items():
    label_color = PAGE_BG if data["group"] != "data" else INK
    ax.text(
        data["pos"][0],
        data["pos"][1],
        name,
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color=label_color,
        zorder=3,
    )

# Create legend
legend_handles = [
    plt.scatter([], [], c=[group_colors[g]], s=400, label=g.capitalize(), edgecolors=PAGE_BG, linewidths=2)
    for g in groups
]
legend_handles.append(plt.Line2D([0], [0], color=INK_SOFT, linewidth=1.6, label="Weak (1)", alpha=0.6))
legend_handles.append(plt.Line2D([0], [0], color=INK_SOFT, linewidth=4.0, label="Strong (5)", alpha=0.9))

ax.legend(
    handles=legend_handles,
    loc="upper left",
    fontsize=14,
    title="Module Type / Edge Weight",
    title_fontsize=16,
    framealpha=0.95,
    markerscale=1.0,
    borderpad=1,
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
)

# Styling
ax.set_title("network-directed · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.08, 1.02)
ax.axis("off")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
