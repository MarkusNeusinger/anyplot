"""anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: Simulated permutation importance (resembles sklearn.inspection output)
np.random.seed(42)

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

importance_mean = np.array([0.032, 0.003, -0.002, 0.008, 0.012, 0.048, 0.142, 0.001, 0.018, 0.095, 0.055, 0.068, 0.105])
importance_std = np.array([0.015, 0.008, 0.006, 0.010, 0.009, 0.020, 0.025, 0.005, 0.012, 0.022, 0.018, 0.019, 0.023])

# Sort by importance (highest at top)
sorted_idx = np.argsort(importance_mean)
feature_names_sorted = [feature_names[i] for i in sorted_idx]
importance_mean_sorted = importance_mean[sorted_idx]
importance_std_sorted = importance_std[sorted_idx]

# Color gradient based on importance values
norm = plt.Normalize(importance_mean_sorted.min(), importance_mean_sorted.max())
cmap = plt.cm.Blues
colors = cmap(norm(importance_mean_sorted))

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

y_pos = np.arange(len(feature_names_sorted))
ax.barh(
    y_pos,
    importance_mean_sorted,
    xerr=importance_std_sorted,
    color=colors,
    edgecolor=INK_SOFT,
    linewidth=1.5,
    height=0.7,
    capsize=5,
    error_kw={"elinewidth": 2, "capthick": 2, "ecolor": INK_SOFT},
)

# Reference line at x=0
ax.axvline(x=0, color=INK_SOFT, linewidth=2, linestyle="-", alpha=0.8)

# Styling
ax.set_yticks(y_pos)
ax.set_yticklabels(feature_names_sorted, fontsize=16, color=INK_SOFT)
ax.set_xlabel("Mean Decrease in Accuracy", fontsize=20, color=INK)
ax.set_ylabel("Feature", fontsize=20, color=INK)
ax.set_title("bar-permutation-importance · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT)
ax.tick_params(axis="y", colors=INK_SOFT)

# Grid
ax.grid(True, axis="x", alpha=0.15, linestyle="-", linewidth=0.8, color=INK)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.02)
cbar.set_label("Importance", fontsize=16, color=INK)
cbar.ax.tick_params(labelsize=14, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
