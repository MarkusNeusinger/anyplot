""" pyplots.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Modeling diminishing returns (economics example)
np.random.seed(42)
x = np.linspace(0, 10, 80)
# Quadratic relationship: y = -0.5x² + 6x + 5 + noise
y = -0.5 * x**2 + 6 * x + 5 + np.random.normal(0, 2, len(x))

# Fit polynomial regression (degree 2 - quadratic)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)
x_smooth = np.linspace(x.min(), x.max(), 200)
y_fit = poly(x_smooth)

# Calculate R² value
y_pred = poly(x)
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Create plot (4800x2700 px at 300 dpi = 16x9 inches)
fig, ax = plt.subplots(figsize=(16, 9))

# Scatter points with transparency
ax.scatter(x, y, s=150, alpha=0.6, color="#306998", edgecolors="white", linewidths=0.5, label="Data points", zorder=3)

# Confidence band (approximate using residual standard error)
residuals = y - y_pred
std_err = np.std(residuals)
ax.fill_between(
    x_smooth,
    y_fit - 1.96 * std_err,
    y_fit + 1.96 * std_err,
    alpha=0.2,
    color="#FFD43B",
    label="95% confidence band",
    zorder=1,
)

# Polynomial regression curve
ax.plot(x_smooth, y_fit, color="#FFD43B", linewidth=3.5, label="Polynomial fit (degree 2)", zorder=2)

# Format polynomial equation
a, b, c = coeffs
equation = f"y = {a:.2f}x² + {b:.2f}x + {c:.2f}"

# Add R² and equation annotation
annotation_text = f"{equation}\nR² = {r_squared:.3f}"
ax.annotate(
    annotation_text,
    xy=(0.03, 0.97),
    xycoords="axes fraction",
    fontsize=16,
    verticalalignment="top",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "edgecolor": "gray", "alpha": 0.9},
)

# Labels and styling
ax.set_xlabel("Investment (units)", fontsize=20)
ax.set_ylabel("Return (units)", fontsize=20)
ax.set_title("scatter-regression-polynomial · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="lower right")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
