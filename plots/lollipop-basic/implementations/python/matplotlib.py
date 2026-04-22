""" pyplots.ai
lollipop-basic: Basic Lollipop Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Product sales by category, sorted by value
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Beauty",
    "Automotive",
    "Food & Beverages",
    "Office Supplies",
]
values = [87, 72, 65, 58, 52, 45, 41, 38, 32, 25]

# Sort by value descending for better readability
sorted_indices = np.argsort(values)[::-1]
categories = [categories[i] for i in sorted_indices]
values = [values[i] for i in sorted_indices]

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

# Plot lollipop chart: stems + markers
x_positions = np.arange(len(categories))
ax.vlines(x_positions, ymin=0, ymax=values, color="#306998", linewidth=2.5)
ax.scatter(x_positions, values, color="#FFD43B", s=300, zorder=3, edgecolors="#306998", linewidths=2)

# Labels and styling (scaled for 4800x2700)
ax.set_xlabel("Product Category", fontsize=20)
ax.set_ylabel("Sales (thousands)", fontsize=20)
ax.set_title("lollipop-basic · matplotlib · pyplots.ai", fontsize=24)

ax.set_xticks(x_positions)
ax.set_xticklabels(categories, rotation=45, ha="right", fontsize=16)
ax.tick_params(axis="y", labelsize=16)

ax.set_ylim(0, max(values) * 1.1)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
