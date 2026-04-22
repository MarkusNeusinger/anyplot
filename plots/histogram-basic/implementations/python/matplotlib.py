""" pyplots.ai
histogram-basic: Basic Histogram
Library: matplotlib 3.10.8 | Python 3.14.0
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba


# Data - Simulate exam scores with slight left skew (realistic grade distribution)
np.random.seed(42)
base = np.random.normal(loc=72, scale=12, size=450)
high_cluster = np.random.normal(loc=88, scale=4, size=50)
scores = np.clip(np.concatenate([base, high_cluster]), 0, 100)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
n, bins, patches = ax.hist(scores, bins=25, color="#306998", edgecolor="white", linewidth=1.5, alpha=0.85)

# Shade bars by height using patch manipulation (matplotlib-distinctive)
max_count = max(n)
base_color = to_rgba("#306998")
for count, patch in zip(n, patches, strict=True):
    intensity = 0.5 + 0.5 * (count / max_count)
    patch.set_facecolor((*base_color[:3], intensity * 0.85))

# Data storytelling: annotate key distribution features
mean_score = np.mean(scores)
median_score = np.median(scores)
y_max = max(n)

# Mean line with annotation
ax.axvline(mean_score, color="#E34F26", linewidth=2.5, linestyle="--", zorder=5)
ax.annotate(
    f"Mean: {mean_score:.1f}",
    xy=(mean_score, y_max * 0.92),
    xytext=(mean_score - 18, y_max * 0.96),
    fontsize=15,
    fontweight="bold",
    color="#E34F26",
    arrowprops={"arrowstyle": "->", "color": "#E34F26", "lw": 1.8},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#E34F26", "alpha": 0.9},
    zorder=6,
)

# Median line with annotation
ax.axvline(median_score, color="#4B8BBE", linewidth=2.5, linestyle=":", zorder=5)
ax.annotate(
    f"Median: {median_score:.1f}",
    xy=(median_score, y_max * 0.82),
    xytext=(median_score + 8, y_max * 0.88),
    fontsize=15,
    fontweight="bold",
    color="#4B8BBE",
    arrowprops={"arrowstyle": "->", "color": "#4B8BBE", "lw": 1.8},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#4B8BBE", "alpha": 0.9},
    zorder=6,
)

# Highlight high-performer cluster with a bracket annotation
ax.annotate(
    "High-performer\ncluster",
    xy=(88, y_max * 0.35),
    xytext=(95, y_max * 0.60),
    fontsize=14,
    fontstyle="italic",
    color="#555555",
    ha="center",
    arrowprops={"arrowstyle": "->", "color": "#555555", "lw": 1.5, "connectionstyle": "arc3,rad=-0.2"},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "#FFF9C4", "edgecolor": "#CCCCCC", "alpha": 0.9},
    zorder=6,
)

# Shade the high-performer region using axvspan (matplotlib-distinctive)
ax.axvspan(80, 100, alpha=0.06, color="#FFB300", zorder=0)

# Labels and styling
ax.set_xlabel("Exam Score (points)", fontsize=20)
ax.set_ylabel("Frequency (count)", fontsize=20)
ax.set_title("histogram-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)

# Spine removal (library convention: remove top + right)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Subtle y-axis grid
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_axisbelow(True)

# Ensure y-axis starts at zero
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
