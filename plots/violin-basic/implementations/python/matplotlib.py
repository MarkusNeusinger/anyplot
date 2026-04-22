""" pyplots.ai
violin-basic: Basic Violin Plot
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 92/100 | Updated: 2026-02-21
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np


# Data - simulated test scores (0-100) across different schools
np.random.seed(42)
categories = ["Lincoln HS", "Roosevelt Acad.", "Jefferson HS", "Hamilton Prep"]
data = [
    np.clip(np.random.normal(75, 10, 150), 0, 100),  # Lincoln: normal, centered ~75
    np.clip(np.random.normal(85, 6, 150), 0, 100),  # Roosevelt: high, tight cluster
    np.clip(np.random.normal(62, 15, 150), 0, 100),  # Jefferson: lower, wide spread
    np.clip(
        np.concatenate([np.random.normal(70, 5, 80), np.random.normal(88, 4, 70)]), 0, 100
    ),  # Hamilton: bimodal (two subgroups)
]

# Multi-series palette starting with Python Blue; warm accent for bimodal Hamilton
colors = ["#306998", "#5BA58B", "#7A6FB5", "#D4853F"]
edge_colors = ["#1E4060", "#3A7460", "#524A80", "#9A5F2A"]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

parts = ax.violinplot(
    data,
    positions=range(len(categories)),
    quantiles=[[0.25, 0.5, 0.75]] * len(categories),
    showmeans=False,
    showmedians=False,
    showextrema=False,
    bw_method=0.3,
    widths=0.75,
)

# Style each violin body with a distinct color
for i, pc in enumerate(parts["bodies"]):
    pc.set_facecolor(colors[i])
    pc.set_edgecolor(edge_colors[i])
    pc.set_alpha(0.8)
    pc.set_linewidth(2)

# Quantile lines with path effects for legibility against colored bodies
q_colors = ["white", "#FFD43B", "white"] * len(categories)
q_widths = [2.5, 4, 2.5] * len(categories)
parts["cquantiles"].set_colors(q_colors)
parts["cquantiles"].set_linewidths(q_widths)
parts["cquantiles"].set_path_effects([pe.Stroke(linewidth=6, foreground="black", alpha=0.3), pe.Normal()])

# Labels and styling
ax.set_xticks(range(len(categories)))
ax.set_xticklabels(categories)
ax.set_xlabel("School", fontsize=20)
ax.set_ylabel("Test Score (points)", fontsize=20)
ax.set_title("violin-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)

# Subtle annotation highlighting Hamilton Prep's bimodal distribution
ax.annotate(
    "Two distinct\nperformance groups",
    xy=(3, 75),
    xytext=(3, 45),
    fontsize=13,
    color="#9A5F2A",
    fontstyle="italic",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#9A5F2A", "lw": 1.5},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
