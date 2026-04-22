""" pyplots.ai
raincloud-basic: Basic Raincloud Plot
Library: seaborn 0.13.2 | Python 3.14
Quality: 90/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import PathPatch


# Data - Reaction times (ms) for different experimental conditions
np.random.seed(42)

control = np.random.normal(450, 60, 80)
treatment_a = np.random.normal(380, 50, 80)  # Faster, less variable
treatment_b = np.concatenate(
    [  # Bimodal - shows advantage of raincloud over box plots
        np.random.normal(350, 30, 50),
        np.random.normal(480, 40, 30),
    ]
)

data = pd.DataFrame(
    {
        "Condition": ["Control"] * len(control)
        + ["Treatment A"] * len(treatment_a)
        + ["Treatment B"] * len(treatment_b),
        "Reaction Time": np.concatenate([control, treatment_a, treatment_b]),
    }
)

# Create figure - HORIZONTAL orientation: x=values, y=categories
fig, ax = plt.subplots(figsize=(16, 9))

palette = {"Control": "#306998", "Treatment A": "#E6A800", "Treatment B": "#4DAF4A"}
order = ["Control", "Treatment A", "Treatment B"]

# Cloud (half-violin) - use seaborn's violinplot then clip to upper half
sns.violinplot(
    data=data,
    x="Reaction Time",
    y="Condition",
    hue="Condition",
    palette=palette,
    order=order,
    cut=0,
    inner=None,
    density_norm="width",
    width=0.7,
    linewidth=1.5,
    ax=ax,
    legend=False,
)

# Clip violins to show only top half (cloud above baseline)
for i, collection in enumerate(ax.collections):
    paths = collection.get_paths()
    for path in paths:
        vertices = path.vertices
        center = i
        mask = vertices[:, 1] >= center
        vertices[~mask, 1] = center

# Box plot - centered on category baseline
colors = [palette[c] for c in order]
sns.boxplot(
    data=data,
    x="Reaction Time",
    y="Condition",
    hue="Condition",
    palette=palette,
    order=order,
    width=0.12,
    showfliers=False,
    linewidth=2,
    boxprops={"facecolor": "white", "zorder": 4},
    medianprops={"linewidth": 2.5, "zorder": 5},
    whiskerprops={"linewidth": 2, "zorder": 4},
    capprops={"linewidth": 2, "zorder": 4},
    ax=ax,
    legend=False,
)

# Color box elements to match their category for visual cohesion
box_patches = [c for c in ax.get_children() if isinstance(c, PathPatch)]
for i, patch in enumerate(box_patches):
    color = colors[i]
    patch.set_edgecolor(color)
    patch.set_facecolor("white")

# Color whiskers, caps, and medians (5 lines per box: 2 whiskers, 2 caps, 1 median)
lines = ax.get_lines()
lines_per_box = 5
for i in range(len(order)):
    color = colors[i]
    for j in range(lines_per_box):
        idx = i * lines_per_box + j
        if idx < len(lines):
            lines[idx].set_color(color)
            lines[idx].set_zorder(4)

# Rain (jittered points) - below category baseline
for i, condition in enumerate(order):
    subset = data[data["Condition"] == condition]["Reaction Time"].values
    color = palette[condition]
    jitter = np.random.uniform(-0.06, 0.06, len(subset))
    ax.scatter(subset, i - 0.25 + jitter, s=55, alpha=0.6, color=color, edgecolor="white", linewidth=0.5, zorder=3)

# Styling
ax.set_xlabel("Reaction Time (ms)", fontsize=20, labelpad=12)
ax.set_ylabel("Condition", fontsize=20, labelpad=12)
ax.set_title("raincloud-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20)

ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="x", alpha=0.2, linestyle="--", linewidth=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.8)
ax.spines["bottom"].set_linewidth(0.8)

ax.set_ylim(-0.5, 2.6)

# Data Storytelling: annotate the bimodal distribution in Treatment B

ax.annotate(
    "Bimodal distribution\nrevealed by raincloud",
    xy=(475, 2.15),
    xytext=(530, 1.3),
    fontsize=13,
    fontweight="medium",
    color="#333333",
    ha="left",
    arrowprops={"arrowstyle": "->", "color": "#666666", "linewidth": 1.5, "connectionstyle": "arc3,rad=-0.2"},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

# Annotate Treatment A showing faster responses
ta_median = np.median(data[data["Condition"] == "Treatment A"]["Reaction Time"])
ctrl_median = np.median(data[data["Condition"] == "Control"]["Reaction Time"])
diff_ms = ctrl_median - ta_median

ax.annotate(
    f"~{diff_ms:.0f} ms faster\nthan Control",
    xy=(ta_median, 1),
    xytext=(280, 0.3),
    fontsize=13,
    fontweight="medium",
    color="#333333",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#666666", "linewidth": 1.5, "connectionstyle": "arc3,rad=0.2"},
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
