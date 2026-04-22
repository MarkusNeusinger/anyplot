""" pyplots.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 95/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
from statsmodels.nonparametric.smoothers_lowess import lowess


# Data - create a non-linear relationship that varies across x-axis range
np.random.seed(42)
n_points = 200
x = np.linspace(0, 10, n_points)
# Complex non-linear pattern: sine wave + quadratic trend + noise
y = 2 * np.sin(x * 0.8) + 0.15 * x**2 + np.random.normal(0, 0.8, n_points)

# Compute LOWESS smoothed curve
lowess_result = lowess(y, x, frac=0.3, return_sorted=True)
x_smooth = lowess_result[:, 0]
y_smooth = lowess_result[:, 1]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Scatter points with transparency
ax.scatter(x, y, s=100, alpha=0.6, color="#306998", edgecolors="white", linewidth=0.5, label="Data points")

# LOWESS regression curve
ax.plot(x_smooth, y_smooth, color="#FFD43B", linewidth=4, label="LOWESS fit", solid_capstyle="round")

# Labels and styling
ax.set_xlabel("Measurement Index", fontsize=20)
ax.set_ylabel("Response Value", fontsize=20)
ax.set_title("scatter-regression-lowess · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
