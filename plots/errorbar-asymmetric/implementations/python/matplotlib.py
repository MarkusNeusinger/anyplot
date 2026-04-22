""" pyplots.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Monthly sales performance with asymmetric confidence intervals (10th-90th percentile)
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
sales = np.array([42, 55, 48, 61, 73, 68, 82, 78])  # Median sales (thousands)

# Asymmetric errors: lower bound is smaller (more confident), upper bound is larger (more uncertain)
error_lower = np.array([5, 8, 6, 9, 7, 10, 8, 6])  # Distance below median
error_upper = np.array([12, 15, 10, 18, 14, 20, 16, 12])  # Distance above median

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot error bars with asymmetric errors
# yerr expects [lower, upper] arrays
ax.errorbar(
    months,
    sales,
    yerr=[error_lower, error_upper],
    fmt="o",
    markersize=15,
    color="#306998",
    ecolor="#306998",
    elinewidth=3,
    capsize=10,
    capthick=3,
    alpha=0.9,
    label="Median with 10th-90th percentile",
)

# Add a subtle fill to show the confidence region
x_positions = np.arange(len(months))
ax.fill_between(x_positions, sales - error_lower, sales + error_upper, alpha=0.15, color="#306998")

# Styling
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Sales (thousands USD)", fontsize=20)
ax.set_title("errorbar-asymmetric · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper left")
ax.grid(True, alpha=0.3, linestyle="--")

# Set y-axis limits to give some padding
ax.set_ylim(0, 120)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
