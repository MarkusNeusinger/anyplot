""" pyplots.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec


# Data - correlated bivariate data with realistic pattern
np.random.seed(42)
n = 200

# Create correlated data with some structure
x = np.concatenate(
    [
        np.random.normal(30, 8, n // 2),  # First cluster
        np.random.normal(60, 10, n // 2),  # Second cluster
    ]
)
y = 0.7 * x + np.random.normal(0, 8, n) + 10  # Linear relationship with noise

# Create figure with GridSpec for layout
fig = plt.figure(figsize=(16, 9))
gs = GridSpec(4, 4, figure=fig, hspace=0.05, wspace=0.05)

# Main scatter plot (lower-left, 3x3)
ax_main = fig.add_subplot(gs[1:4, 0:3])
ax_main.scatter(x, y, s=120, alpha=0.65, color="#306998", edgecolors="white", linewidth=0.5)
ax_main.set_xlabel("X Value", fontsize=20)
ax_main.set_ylabel("Y Value", fontsize=20)
ax_main.tick_params(axis="both", labelsize=16)
ax_main.grid(True, alpha=0.3, linestyle="--")

# Top marginal histogram (aligned with main x-axis)
ax_top = fig.add_subplot(gs[0, 0:3], sharex=ax_main)
ax_top.hist(x, bins=25, color="#306998", alpha=0.7, edgecolor="white", linewidth=0.8)
ax_top.tick_params(axis="x", labelbottom=False)
ax_top.tick_params(axis="y", labelsize=14)
ax_top.set_ylabel("Count", fontsize=16)
ax_top.spines["top"].set_visible(False)
ax_top.spines["right"].set_visible(False)

# Right marginal histogram (aligned with main y-axis)
ax_right = fig.add_subplot(gs[1:4, 3], sharey=ax_main)
ax_right.hist(y, bins=25, orientation="horizontal", color="#306998", alpha=0.7, edgecolor="white", linewidth=0.8)
ax_right.tick_params(axis="y", labelleft=False)
ax_right.tick_params(axis="x", labelsize=14)
ax_right.set_xlabel("Count", fontsize=16)
ax_right.spines["top"].set_visible(False)
ax_right.spines["right"].set_visible(False)

# Title in the top-right corner area
fig.text(
    0.98, 0.98, "scatter-marginal · matplotlib · pyplots.ai", fontsize=24, ha="right", va="top", fontweight="normal"
)

plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
