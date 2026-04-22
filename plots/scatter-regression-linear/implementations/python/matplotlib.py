""" pyplots.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Study hours vs exam scores (realistic educational context)
np.random.seed(42)
n_points = 80
x = np.random.uniform(1, 10, n_points)  # Study hours (1-10)
noise = np.random.normal(0, 8, n_points)
y = 35 + 6 * x + noise  # Exam scores: base 35 + 6 points per hour
y = np.clip(y, 20, 100)  # Realistic score range

# Linear regression using numpy
x_mean, y_mean = np.mean(x), np.mean(y)
ss_xx = np.sum((x - x_mean) ** 2)
ss_xy = np.sum((x - x_mean) * (y - y_mean))
slope = ss_xy / ss_xx
intercept = y_mean - slope * x_mean

# Calculate R-squared
y_pred = slope * x + intercept
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - y_mean) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Regression line and confidence interval
x_line = np.linspace(x.min() - 0.5, x.max() + 0.5, 100)
y_line = slope * x_line + intercept

# Calculate 95% confidence interval
n = len(x)
se_y = np.sqrt(ss_res / (n - 2))  # Standard error of regression
se_line = se_y * np.sqrt(1 / n + (x_line - x_mean) ** 2 / ss_xx)
# t-value for 95% CI with n-2 degrees of freedom (approximately 1.99 for n=80)
t_val = 1.99
ci_upper = y_line + t_val * se_line
ci_lower = y_line - t_val * se_line

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Confidence interval band
ax.fill_between(x_line, ci_lower, ci_upper, alpha=0.25, color="#FFD43B", label="95% CI")

# Scatter points
ax.scatter(x, y, s=150, alpha=0.7, color="#306998", edgecolors="white", linewidths=0.5, zorder=3)

# Regression line
ax.plot(x_line, y_line, color="#E74C3C", linewidth=3, label="Regression Line", zorder=2)

# Annotations
equation = f"y = {slope:.2f}x + {intercept:.2f}"
r_text = f"R² = {r_squared:.3f}"
ax.text(
    0.05,
    0.95,
    f"{equation}\n{r_text}",
    transform=ax.transAxes,
    fontsize=18,
    verticalalignment="top",
    bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "gray", "alpha": 0.9},
)

# Styling
ax.set_xlabel("Study Hours", fontsize=20)
ax.set_ylabel("Exam Score", fontsize=20)
ax.set_title("scatter-regression-linear · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="lower right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
