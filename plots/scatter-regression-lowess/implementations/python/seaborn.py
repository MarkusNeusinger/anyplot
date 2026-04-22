""" pyplots.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - create non-linear relationship with varying patterns
np.random.seed(42)
n_points = 200
x = np.linspace(0, 10, n_points)
# Complex non-linear relationship: combination of sine wave and quadratic
y = 2 * np.sin(x) + 0.3 * x**1.5 + np.random.normal(0, 0.8, n_points)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Scatter plot with LOWESS regression using seaborn's regplot
# lowess=True enables LOWESS (locally weighted scatterplot smoothing)
sns.regplot(
    x=x,
    y=y,
    lowess=True,
    scatter_kws={"alpha": 0.6, "s": 100, "color": "#306998"},
    line_kws={"color": "#FFD43B", "linewidth": 4},
    ax=ax,
)

# Styling
ax.set_xlabel("X Value", fontsize=20)
ax.set_ylabel("Y Value", fontsize=20)
ax.set_title("scatter-regression-lowess · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
