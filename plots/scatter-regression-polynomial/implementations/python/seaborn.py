""" pyplots.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Simulate diminishing returns scenario (investment vs profit)
np.random.seed(42)
n_points = 80
x = np.linspace(0, 10, n_points)
# Quadratic relationship with diminishing returns: y = -0.8x² + 10x + 5 + noise
y = -0.8 * x**2 + 10 * x + 5 + np.random.randn(n_points) * 3

# Fit polynomial regression (degree 2 - quadratic)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)
y_pred = poly(x)

# Calculate R² score
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r2 = 1 - (ss_res / ss_tot)

# Get coefficients for equation display (coeffs = [a, b, c] for ax² + bx + c)
a, b, c = coeffs

# Generate smooth curve for plotting
x_smooth = np.linspace(x.min(), x.max(), 200)
y_smooth = poly(x_smooth)

# Calculate confidence band based on residual standard error
residuals = y - y_pred
std_err = np.std(residuals)

# Plot
sns.set_style("whitegrid")
fig, ax = plt.subplots(figsize=(16, 9))

# Scatter points with seaborn
sns.scatterplot(
    x=x, y=y, ax=ax, s=150, alpha=0.65, color="#306998", edgecolor="white", linewidth=0.5, label="Data Points"
)

# Polynomial regression line
ax.plot(x_smooth, y_smooth, color="#FFD43B", linewidth=4, label="Polynomial Fit (degree 2)")

# Confidence band
ax.fill_between(
    x_smooth,
    y_smooth - 1.96 * std_err,
    y_smooth + 1.96 * std_err,
    color="#FFD43B",
    alpha=0.2,
    label="95% Confidence Band",
)

# Equation and R² annotation
sign_b = "+" if b >= 0 else "-"
sign_c = "+" if c >= 0 else "-"
equation = f"y = {a:.2f}x² {sign_b} {abs(b):.2f}x {sign_c} {abs(c):.2f}"
annotation_text = f"{equation}\nR² = {r2:.3f}"
ax.annotate(
    annotation_text,
    xy=(0.03, 0.97),
    xycoords="axes fraction",
    fontsize=18,
    verticalalignment="top",
    horizontalalignment="left",
    bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "alpha": 0.9, "edgecolor": "#cccccc"},
)

# Labels and styling
ax.set_xlabel("Investment (units)", fontsize=20)
ax.set_ylabel("Profit (units)", fontsize=20)
ax.set_title("scatter-regression-polynomial · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="lower right", framealpha=0.9)
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
