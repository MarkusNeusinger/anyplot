""" pyplots.ai
elbow-curve: Elbow Curve for K-Means Clustering
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Simulate realistic inertia values for K-means elbow curve
# Based on typical clustering behavior: sharp decline followed by gradual decrease
np.random.seed(42)
k_values = np.arange(1, 11)

# Generate realistic inertia decay pattern
# Inertia typically follows exponential decay with the "elbow" around k=4
base_inertia = 5000
inertias = []
for k in k_values:
    # Exponential decay with elbow effect at k=4
    if k <= 4:
        inertia = base_inertia * np.exp(-0.35 * (k - 1))
    else:
        inertia = base_inertia * np.exp(-0.35 * 3) * np.exp(-0.15 * (k - 4))
    # Add small random noise for realism
    inertia += np.random.uniform(-50, 50)
    inertias.append(max(inertia, 100))

inertias = np.array(inertias)

# Identify the elbow point (k=4 is the optimal cluster count)
elbow_k = 4
elbow_inertia = inertias[elbow_k - 1]

# Create plot (4800x2700 px at 300 dpi = 16x9 inches)
fig, ax = plt.subplots(figsize=(16, 9))

# Plot the elbow curve
ax.plot(
    k_values,
    inertias,
    color="#306998",
    linewidth=3,
    marker="o",
    markersize=12,
    markerfacecolor="#FFD43B",
    markeredgecolor="#306998",
    markeredgewidth=2,
    label="Inertia",
)

# Highlight the elbow point
ax.scatter([elbow_k], [elbow_inertia], s=400, color="#FFD43B", edgecolors="#306998", linewidths=3, zorder=5)
ax.annotate(
    f"Elbow Point\n(k={elbow_k})",
    xy=(elbow_k, elbow_inertia),
    xytext=(elbow_k + 1.8, elbow_inertia + 600),
    fontsize=18,
    fontweight="bold",
    color="#306998",
    arrowprops={"arrowstyle": "->", "color": "#306998", "lw": 2.5},
)

# Labels and styling
ax.set_xlabel("Number of Clusters (k)", fontsize=20)
ax.set_ylabel("Inertia (Within-Cluster Sum of Squares)", fontsize=20)
ax.set_title("elbow-curve · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xticks(k_values)
ax.grid(True, alpha=0.3, linestyle="--")

# Add subtle shading to show diminishing returns region
ax.axvspan(elbow_k, max(k_values), alpha=0.1, color="#306998", label="Diminishing Returns")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
