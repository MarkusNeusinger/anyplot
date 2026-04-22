""" pyplots.ai
scatter-marginal: Scatter Plot with Marginal Distributions
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
import seaborn as sns


# Data - correlated bivariate data to demonstrate scatter + marginal distributions
np.random.seed(42)
n_points = 200
x = np.random.randn(n_points) * 15 + 50
y = 0.7 * x + np.random.randn(n_points) * 10 + 20

# Create jointplot with scatter and marginal histograms+KDE
sns.set_context("talk", font_scale=1.4)
g = sns.jointplot(
    x=x,
    y=y,
    kind="scatter",
    height=12,
    ratio=5,
    marginal_kws={"bins": 25, "kde": True, "color": "#306998", "alpha": 0.7},
    joint_kws={"s": 150, "alpha": 0.65, "color": "#306998", "edgecolor": "white", "linewidth": 0.5},
)

# Style the central scatter plot
g.ax_joint.set_xlabel("X Value", fontsize=22)
g.ax_joint.set_ylabel("Y Value", fontsize=22)
g.ax_joint.tick_params(axis="both", labelsize=16)
g.ax_joint.grid(True, alpha=0.3, linestyle="--")

# Style marginal plots
g.ax_marg_x.tick_params(axis="both", labelsize=14)
g.ax_marg_y.tick_params(axis="both", labelsize=14)

# Add title to figure
g.figure.suptitle("scatter-marginal · seaborn · pyplots.ai", fontsize=26, y=0.98)
g.figure.subplots_adjust(top=0.92)

# Save at high resolution
g.figure.savefig("plot.png", dpi=300, bbox_inches="tight")
