""" pyplots.ai
histogram-2d: 2D Histogram Heatmap
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - bivariate normal with correlation (5000 points to show density patterns)
np.random.seed(42)
n_points = 5000
mean = [0, 0]
cov = [[1, 0.7], [0.7, 1]]  # Positive correlation
data = np.random.multivariate_normal(mean, cov, n_points)
x = data[:, 0]
y = data[:, 1]

# Create figure with colorbar space
fig, ax = plt.subplots(figsize=(16, 9))

# 2D histogram with perceptually uniform colormap
h = ax.hist2d(
    x,
    y,
    bins=40,
    cmap="viridis",
    cmin=1,  # Don't show empty bins
)

# Add colorbar
cbar = fig.colorbar(h[3], ax=ax, pad=0.02)
cbar.set_label("Count", fontsize=20)
cbar.ax.tick_params(labelsize=16)

# Labels and styling
ax.set_xlabel("X Value", fontsize=20)
ax.set_ylabel("Y Value", fontsize=20)
ax.set_title("histogram-2d · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
