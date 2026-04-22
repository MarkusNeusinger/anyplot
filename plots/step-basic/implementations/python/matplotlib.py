""" pyplots.ai
step-basic: Basic Step Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Monthly cumulative sales figures (realistic scenario)
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Cumulative sales that increase in discrete jumps
monthly_sales = np.array([45, 52, 48, 61, 55, 72, 68, 85, 78, 92, 88, 105])
cumulative_sales = np.cumsum(monthly_sales)

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Step plot with 'post' style - value applies from current point until next
ax.step(months, cumulative_sales, where="post", linewidth=3, color="#306998", label="Cumulative Sales")

# Add markers at data points to highlight where changes occur
ax.scatter(
    months, cumulative_sales, s=200, color="#FFD43B", edgecolor="#306998", linewidth=2, zorder=5, label="Monthly Totals"
)

# Labels and styling
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Cumulative Sales (thousands $)", fontsize=20)
ax.set_title("step-basic · matplotlib · pyplots.ai", fontsize=24)

# Set x-axis ticks to show month labels
ax.set_xticks(months)
ax.set_xticklabels(month_labels)
ax.tick_params(axis="both", labelsize=16)

# Grid for tracing values
ax.grid(True, alpha=0.3, linestyle="--")

# Legend
ax.legend(fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
