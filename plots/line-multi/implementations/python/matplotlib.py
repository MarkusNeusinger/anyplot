""" pyplots.ai
line-multi: Multi-Line Comparison Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Monthly sales (in thousands) for 3 product lines over 12 months
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Product A: Steady growth with seasonal bump in Q4
product_a = 50 + np.arange(12) * 3 + np.array([0, 0, 0, 0, 0, 5, 5, 0, 10, 15, 20, 25])
product_a = product_a + np.random.randn(12) * 3

# Product B: Strong start, mid-year dip, recovery
product_b = 80 + np.array([0, -5, -10, -15, -20, -25, -20, -15, -10, -5, 0, 5])
product_b = product_b + np.random.randn(12) * 4

# Product C: New product launch, exponential growth
product_c = 20 + np.exp(np.arange(12) * 0.15) * 10
product_c = product_c + np.random.randn(12) * 2

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot each series with distinct colors and markers
ax.plot(
    months,
    product_a,
    color="#306998",
    linewidth=3,
    marker="o",
    markersize=10,
    label="Product A (Electronics)",
    linestyle="-",
)
ax.plot(
    months,
    product_b,
    color="#FFD43B",
    linewidth=3,
    marker="s",
    markersize=10,
    label="Product B (Appliances)",
    linestyle="--",
)
ax.plot(
    months,
    product_c,
    color="#E74C3C",
    linewidth=3,
    marker="^",
    markersize=10,
    label="Product C (Software)",
    linestyle="-.",
)

# Labels and styling
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Sales ($ thousands)", fontsize=20)
ax.set_title("line-multi · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set x-axis ticks to show month labels
ax.set_xticks(months)
ax.set_xticklabels(month_labels)

# Grid and legend
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper left", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
