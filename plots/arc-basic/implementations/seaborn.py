""" pyplots.ai
arc-basic: Basic Arc Diagram
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-23
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Data: Character interactions in a story (12 characters)
nodes = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack", "Kate", "Leo"]
n_nodes = len(nodes)

# Edges: (source_index, target_index, interaction_weight)
edges = [
    (0, 1, 5),  # Alice – Bob
    (0, 3, 2),  # Alice – Dave
    (1, 2, 4),  # Bob – Carol
    (1, 4, 3),  # Bob – Eve
    (2, 5, 2),  # Carol – Frank
    (3, 4, 5),  # Dave – Eve
    (3, 6, 3),  # Dave – Grace
    (4, 7, 4),  # Eve – Henry
    (5, 6, 2),  # Frank – Grace
    (0, 11, 1),  # Alice – Leo (long-range)
    (2, 6, 3),  # Carol – Grace
    (1, 5, 2),  # Bob – Frank
    (7, 8, 4),  # Henry – Ivy
    (8, 9, 3),  # Ivy – Jack
    (9, 10, 5),  # Jack – Kate
    (10, 11, 2),  # Kate – Leo
    (6, 9, 2),  # Grace – Jack
    (5, 10, 1),  # Frank – Kate (long-range)
]

x_positions = np.arange(n_nodes)

# Build long-form DataFrame of arc coordinates for seaborn lineplot
arc_rows = []
n_pts = 80
for eid, (src, tgt, w) in enumerate(edges):
    x1, x2 = x_positions[src], x_positions[tgt]
    dist = abs(x2 - x1)
    h = dist * 0.4
    t = np.linspace(0, np.pi, n_pts)
    cx, rx = (x1 + x2) / 2, dist / 2
    arc_x = cx + rx * np.cos(np.pi - t)
    arc_y = h * np.sin(t)
    for xi, yi in zip(arc_x, arc_y, strict=True):
        arc_rows.append({"x": xi, "y": yi, "weight": w, "edge_id": eid})

arc_df = pd.DataFrame(arc_rows)

# Categorize weights for seaborn hue encoding
strength_names = {1: "1 · Weak", 2: "2 · Light", 3: "3 · Moderate", 4: "4 · Strong", 5: "5 · Intense"}
cat_order = [strength_names[k] for k in sorted(strength_names)]
arc_df["strength"] = pd.Categorical(arc_df["weight"].map(strength_names), categories=cat_order, ordered=True)

# Theme
sns.set_theme(style="white", context="talk", font_scale=1.1)
fig, ax = plt.subplots(figsize=(16, 9))

# Viridis palette (reversed so stronger connections = darker/more prominent)
viridis = sns.color_palette("viridis", as_cmap=True)
palette = [viridis(v) for v in [0.82, 0.66, 0.48, 0.30, 0.12]]

# Draw arcs via seaborn lineplot (hue=color by strength, size=thickness by weight)
sns.lineplot(
    data=arc_df,
    x="x",
    y="y",
    hue="strength",
    size="weight",
    units="edge_id",
    estimator=None,
    palette=palette,
    sizes=(2.0, 6.0),
    alpha=0.7,
    ax=ax,
    sort=False,
)

# Keep only color legend entries (remove redundant size entries)
handles, labels = ax.get_legend_handles_labels()
cat_set = set(cat_order)
filtered = [(h, lab) for h, lab in zip(handles, labels, strict=True) if lab in cat_set]
ax.legend(
    [h for h, _ in filtered],
    [lab for _, lab in filtered],
    title="Interaction Strength",
    title_fontsize=20,
    fontsize=16,
    loc="upper right",
    frameon=True,
    fancybox=True,
    framealpha=0.9,
    edgecolor="#cccccc",
)

# Draw nodes with seaborn scatterplot
node_df = pd.DataFrame({"x": x_positions, "y": np.zeros(n_nodes)})
sns.scatterplot(
    data=node_df, x="x", y="y", s=600, color="#306998", zorder=5, ax=ax, legend=False, edgecolor="white", linewidth=1.5
)

# Node labels below the baseline
for i, name in enumerate(nodes):
    ax.text(x_positions[i], -0.22, name, ha="center", va="top", fontsize=16, fontweight="medium", color="#306998")

# Storytelling: highlight the contrast between arc distance and weight
# The tallest arc (Alice–Leo) is the weakest connection
ax.annotate(
    "Weakest link, longest reach",
    xy=(5.5, 4.2),
    fontsize=13,
    fontstyle="italic",
    color="#555555",
    ha="center",
    xytext=(2.0, 4.9),
    arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.0},
)
# Three strongest bonds are all between nearest neighbors
ax.annotate(
    "Strongest local bonds",
    xy=(3.5, 0.42),
    fontsize=13,
    fontstyle="italic",
    color="#555555",
    ha="center",
    xytext=(6.0, 2.0),
    arrowprops={"arrowstyle": "->", "color": "#888888", "lw": 1.0},
)

# Axis styling
ax.set_xlim(-0.8, n_nodes - 0.2)
ax.set_ylim(-0.45, 5.6)
ax.set_title("arc-basic \u00b7 seaborn \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.set_xlabel("")
ax.set_ylabel("")
sns.despine(ax=ax, left=True, bottom=True)
ax.set_xticks([])
ax.set_yticks([])

# Subtle horizontal baseline
ax.axhline(y=0, color="#306998", linewidth=2, alpha=0.3, zorder=1)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
