""" pyplots.ai
cat-box-strip: Box Plot with Strip Overlay
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Generate groups with different distributions to showcase features
np.random.seed(42)

categories = ["Control", "Treatment A", "Treatment B", "Treatment C"]
n_points = [35, 40, 30, 45]  # Different sample sizes per group

# Create varied distributions to show boxplot features
data = {
    "Control": np.random.normal(50, 8, n_points[0]),
    "Treatment A": np.random.normal(65, 12, n_points[1]),  # Higher mean, more spread
    "Treatment B": np.concatenate(
        [  # Bimodal with outliers
            np.random.normal(45, 5, n_points[2] - 3),
            np.array([15, 80, 82]),  # Outliers
        ]
    ),
    "Treatment C": np.random.normal(55, 6, n_points[3]),  # Moderate
}

# Prepare data for plotting
box_data = [data[cat] for cat in categories]
positions = np.arange(len(categories)) + 1

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Box plot
ax.boxplot(
    box_data,
    positions=positions,
    tick_labels=categories,
    widths=0.5,
    patch_artist=True,
    boxprops={"facecolor": "#306998", "alpha": 0.4, "linewidth": 2},
    medianprops={"color": "#FFD43B", "linewidth": 3},
    whiskerprops={"color": "#306998", "linewidth": 2},
    capprops={"color": "#306998", "linewidth": 2},
    flierprops={"marker": "o", "markerfacecolor": "#306998", "markersize": 10, "alpha": 0.7},
)

# Strip plot overlay - add jittered points
for pos, cat in zip(positions, categories, strict=True):
    y = data[cat]
    # Jitter x positions
    x = np.random.normal(pos, 0.08, len(y))
    ax.scatter(x, y, s=100, alpha=0.6, color="#306998", edgecolor="white", linewidth=1, zorder=3)

# Labels and styling
ax.set_xlabel("Treatment Group", fontsize=20)
ax.set_ylabel("Response Value", fontsize=20)
ax.set_title("cat-box-strip · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="y", alpha=0.3, linestyle="--")

# Adjust y-axis to show all data including outliers
ax.set_ylim(0, 100)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
