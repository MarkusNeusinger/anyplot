""" pyplots.ai
heatmap-basic: Basic Heatmap
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 92/100 | Updated: 2026-02-15
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Monthly performance metrics across departments
np.random.seed(42)
departments = ["Sales", "Marketing", "Engineering", "Support", "Finance", "HR", "Operations"]
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Generate performance data (values 0-100)
data = np.random.randn(len(departments), len(months)) * 20 + 50
# Add patterns to demonstrate heatmap capabilities
data[0, :6] += 20  # Sales strong first half
data[2, 6:] += 25  # Engineering strong second half
data[4, :] = data[4, :] * 0.3 + 70  # Finance consistently stable
data[5, 3:9] -= 15  # HR dip mid-year
# Clip to valid performance range
data = np.clip(data, 5, 95)

# Plot - clustermap groups similar departments via hierarchical clustering
g = sns.clustermap(
    data,
    annot=True,
    fmt=".0f",
    cmap="coolwarm",
    center=50,
    xticklabels=months,
    yticklabels=departments,
    linewidths=1.5,
    linecolor="white",
    annot_kws={"fontsize": 16, "fontweight": "medium"},
    figsize=(16, 10),
    row_cluster=True,
    col_cluster=False,
    dendrogram_ratio=0.08,
    cbar_pos=(0.02, 0.15, 0.03, 0.6),
    cbar_kws={"label": "Performance Score", "ticks": [0, 25, 50, 75, 100]},
    vmin=0,
    vmax=100,
)

# Colorbar styling
g.cax.set_ylabel("Performance Score", fontsize=18, labelpad=10)
g.cax.tick_params(labelsize=14)
g.cax.yaxis.set_label_position("left")

# Labels and title
g.ax_heatmap.set_xlabel("Month", fontsize=20, labelpad=12)
g.ax_heatmap.set_ylabel("Department", fontsize=20, labelpad=12)
g.ax_heatmap.tick_params(axis="x", labelsize=16)
g.ax_heatmap.tick_params(axis="y", labelsize=16, rotation=0)

# Visual refinement - remove heatmap spines for cleaner look
for spine in g.ax_heatmap.spines.values():
    spine.set_visible(False)

# Style the dendrogram
g.ax_row_dendrogram.set_facecolor("#f8f8f8")
for spine in g.ax_row_dendrogram.spines.values():
    spine.set_visible(False)

# Background refinement
g.fig.patch.set_facecolor("#fafafa")
g.ax_heatmap.set_facecolor("white")

# Title
g.fig.suptitle("heatmap-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", y=1.02, color="#333333")

plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=g.fig.get_facecolor())
