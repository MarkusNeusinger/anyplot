"""pyplots.ai
dendrogram-basic: Basic Dendrogram
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 88/100 | Updated: 2026-04-05
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from scipy.cluster.hierarchy import dendrogram, linkage, set_link_color_palette


# Data - Iris flower measurements (4 features for 15 samples)
np.random.seed(42)

samples_per_species = 5
labels = []
data = []

# Setosa: shorter petals, wider sepals
for i in range(samples_per_species):
    labels.append(f"Setosa-{i + 1}")
    data.append(
        [
            5.0 + np.random.randn() * 0.3,
            3.4 + np.random.randn() * 0.3,
            1.5 + np.random.randn() * 0.2,
            0.3 + np.random.randn() * 0.1,
        ]
    )

# Versicolor: medium measurements
for i in range(samples_per_species):
    labels.append(f"Versicolor-{i + 1}")
    data.append(
        [
            5.9 + np.random.randn() * 0.4,
            2.8 + np.random.randn() * 0.3,
            4.3 + np.random.randn() * 0.4,
            1.3 + np.random.randn() * 0.2,
        ]
    )

# Virginica: longer petals and sepals
for i in range(samples_per_species):
    labels.append(f"Virginica-{i + 1}")
    data.append(
        [
            6.6 + np.random.randn() * 0.5,
            3.0 + np.random.randn() * 0.3,
            5.5 + np.random.randn() * 0.5,
            2.0 + np.random.randn() * 0.3,
        ]
    )

data = np.array(data)

# Compute hierarchical clustering using Ward's method
linkage_matrix = linkage(data, method="ward")

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor="white")
ax.set_facecolor("#FAFAFA")

# Custom cluster colors via set_link_color_palette (matplotlib/scipy integration)
cluster_colors = ["#306998", "#D4722A", "#3A8A5C"]
set_link_color_palette(cluster_colors)

# Set threshold between the 2nd and 3rd highest merge distances to reveal 3 clusters
sorted_distances = sorted(linkage_matrix[:, 2])
color_threshold = (sorted_distances[-2] + sorted_distances[-3]) / 2

dendro = dendrogram(
    linkage_matrix,
    labels=labels,
    ax=ax,
    leaf_rotation=40,
    leaf_font_size=16,
    above_threshold_color="#AAAAAA",
    color_threshold=color_threshold,
)

# Post-render enhancement: adjust line widths via LineCollection traversal
for child in ax.get_children():
    if isinstance(child, LineCollection):
        child.set_linewidths(3.0)
        child.set_capstyle("round")
        child.set_joinstyle("round")

# Style
ax.set_xlabel("Iris Sample", fontsize=20, labelpad=10)
ax.set_ylabel("Ward Linkage Distance", fontsize=20, labelpad=10)
ax.set_title(
    "Iris Species Clustering · dendrogram-basic · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    pad=20,
    color="#333333",
)
ax.tick_params(axis="both", labelsize=16, colors="#555555")
ax.tick_params(axis="x", labelsize=16, rotation=40)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.6)
ax.spines["left"].set_color("#CCCCCC")
ax.spines["bottom"].set_linewidth(0.6)
ax.spines["bottom"].set_color("#CCCCCC")

# Subtle grid on y-axis only
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color="#888888")
ax.set_axisbelow(True)

plt.tight_layout(pad=1.5)
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
