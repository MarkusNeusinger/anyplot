""" pyplots.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set seaborn style
sns.set_style("whitegrid")

# Simulate realistic elbow curve data
# Inertia decreases with more clusters, with an "elbow" at k=4
np.random.seed(42)
k_values = list(range(1, 11))

# Realistic inertia values showing typical elbow pattern
# High inertia at k=1, sharp decrease until k=4, then diminishing returns
inertias = [
    2800,  # k=1
    1650,  # k=2
    950,  # k=3
    520,  # k=4 - elbow point
    450,  # k=5
    400,  # k=6
    365,  # k=7
    340,  # k=8
    320,  # k=9
    305,  # k=10
]

# Add small noise for realism
noise = np.random.uniform(-10, 10, len(inertias))
inertias = [max(0, i + n) for i, n in zip(inertias, noise, strict=True)]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Plot the elbow curve using seaborn lineplot
sns.lineplot(
    x=k_values,
    y=inertias,
    ax=ax,
    color="#306998",
    linewidth=3,
    marker="o",
    markersize=15,
    markerfacecolor="#FFD43B",
    markeredgecolor="#306998",
    markeredgewidth=2,
)

# Annotate the elbow point (k=4)
elbow_k = 4
elbow_inertia = inertias[elbow_k - 1]
ax.annotate(
    f"Elbow Point (k={elbow_k})",
    xy=(elbow_k, elbow_inertia),
    xytext=(elbow_k + 2, elbow_inertia + 400),
    fontsize=18,
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 2},
    color="#306998",
    fontweight="bold",
)

# Labels and styling
ax.set_xlabel("Number of Clusters (k)", fontsize=20)
ax.set_ylabel("Inertia (Within-Cluster Sum of Squares)", fontsize=20)
ax.set_title("elbow-curve · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xticks(k_values)

# Subtle grid
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
