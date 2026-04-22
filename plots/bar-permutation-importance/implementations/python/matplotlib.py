""" pyplots.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt
import numpy as np


# Simulated permutation importance data (resembles sklearn.inspection output)
np.random.seed(42)

# Feature names representing typical ML model features
feature_names = [
    "alcohol",
    "malic_acid",
    "ash",
    "alcalinity_of_ash",
    "magnesium",
    "total_phenols",
    "flavanoids",
    "nonflavanoid_phenols",
    "proanthocyanins",
    "color_intensity",
    "hue",
    "od280/od315_of_diluted_wines",
    "proline",
]

# Simulated mean importance values (mean decrease in accuracy when feature is shuffled)
# Values range from near-zero to ~0.15 to show typical permutation importance range
importance_mean = np.array([0.032, 0.003, -0.002, 0.008, 0.012, 0.048, 0.142, 0.001, 0.018, 0.095, 0.055, 0.068, 0.105])

# Simulated standard deviations (variability across shuffles)
importance_std = np.array([0.015, 0.008, 0.006, 0.010, 0.009, 0.020, 0.025, 0.005, 0.012, 0.022, 0.018, 0.019, 0.023])

# Sort by importance (highest at top)
sorted_idx = np.argsort(importance_mean)
feature_names_sorted = [feature_names[i] for i in sorted_idx]
importance_mean_sorted = importance_mean[sorted_idx]
importance_std_sorted = importance_std[sorted_idx]

# Create color gradient based on importance values
norm = plt.Normalize(importance_mean_sorted.min(), importance_mean_sorted.max())
cmap = plt.cm.Blues
colors = cmap(norm(importance_mean_sorted))

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

y_pos = np.arange(len(feature_names_sorted))
ax.barh(
    y_pos,
    importance_mean_sorted,
    xerr=importance_std_sorted,
    color=colors,
    edgecolor="#306998",
    linewidth=1.5,
    height=0.7,
    capsize=5,
    error_kw={"elinewidth": 2, "capthick": 2, "ecolor": "#555555"},
)

# Reference line at x=0
ax.axvline(x=0, color="#306998", linewidth=2, linestyle="-", alpha=0.8)

# Styling
ax.set_yticks(y_pos)
ax.set_yticklabels(feature_names_sorted, fontsize=16)
ax.set_xlabel("Mean Decrease in Accuracy", fontsize=20)
ax.set_ylabel("Feature", fontsize=20)
ax.set_title("bar-permutation-importance · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="x", labelsize=16)
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

# Add colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.02)
cbar.set_label("Importance", fontsize=16)
cbar.ax.tick_params(labelsize=14)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
