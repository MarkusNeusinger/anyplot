""" pyplots.ai
histogram-2d: 2D Histogram Heatmap
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import numpy as np
import seaborn as sns


# Data - Bivariate normal distribution with correlation
np.random.seed(42)
n_points = 5000
mean = [0, 0]
cov = [[1, 0.7], [0.7, 1]]  # Correlation of 0.7
data = np.random.multivariate_normal(mean, cov, n_points)
x = data[:, 0]
y = data[:, 1]

# Create figure with marginal histograms using seaborn's histplot with JointGrid
g = sns.JointGrid(x=x, y=y, height=9, ratio=5, marginal_ticks=False)

# Plot 2D histogram heatmap using seaborn's histplot (native seaborn function)
sns.histplot(x=x, y=y, bins=40, cmap="viridis", cbar=True, cbar_kws={"label": "Count"}, ax=g.ax_joint)

# Plot marginal 1D histograms using seaborn's histplot
sns.histplot(x=x, bins=40, color="#306998", alpha=0.8, edgecolor="white", linewidth=0.5, ax=g.ax_marg_x)
sns.histplot(y=y, bins=40, color="#306998", alpha=0.8, edgecolor="white", linewidth=0.5, ax=g.ax_marg_y)

# Styling - scale fonts for large canvas
g.ax_joint.set_xlabel("X Value", fontsize=20)
g.ax_joint.set_ylabel("Y Value", fontsize=20)
g.ax_joint.tick_params(axis="both", labelsize=16)

# Style colorbar
cbar = g.ax_joint.collections[0].colorbar
cbar.ax.tick_params(labelsize=14)
cbar.ax.yaxis.label.set_size(18)

# Title
g.figure.suptitle("histogram-2d · seaborn · pyplots.ai", fontsize=24, y=0.98)

# Hide marginal axis labels for cleaner look
g.ax_marg_x.set_ylabel("")
g.ax_marg_y.set_xlabel("")

# Adjust layout
g.figure.set_size_inches(16, 9)
g.figure.tight_layout()
g.figure.subplots_adjust(top=0.93)

# Save at 4800x2700
g.savefig("plot.png", dpi=300)
