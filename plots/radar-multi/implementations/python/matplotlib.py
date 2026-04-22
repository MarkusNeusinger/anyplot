""" pyplots.ai
radar-multi: Multi-Series Radar Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Product comparison across key attributes
categories = ["Performance", "Battery Life", "Camera", "Display", "Build Quality", "Value"]
products = {
    "Product A": [85, 70, 90, 88, 75, 65],
    "Product B": [72, 95, 78, 82, 88, 80],
    "Product C": [90, 60, 85, 75, 70, 90],
}

# Number of variables
n_categories = len(categories)

# Compute angle for each axis
angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False).tolist()
angles += angles[:1]  # Close the polygon

# Colors: Python Blue, Python Yellow, then additional colorblind-safe
colors = ["#306998", "#FFD43B", "#E377C2"]

# Create figure (square format for radar)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"polar": True})

# Plot each product
for idx, (product, values) in enumerate(products.items()):
    values_closed = values + values[:1]  # Close the polygon
    ax.plot(angles, values_closed, "o-", linewidth=3, label=product, color=colors[idx], markersize=10)
    ax.fill(angles, values_closed, alpha=0.25, color=colors[idx])

# Set category labels at each axis
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=18, fontweight="bold")

# Set radial grid
ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=14, color="gray")

# Grid styling
ax.yaxis.grid(True, linestyle="--", alpha=0.4, linewidth=1.5)
ax.xaxis.grid(True, linestyle="-", alpha=0.3, linewidth=1.5)

# Title
ax.set_title("Product Comparison · radar-multi · matplotlib · pyplots.ai", fontsize=24, fontweight="bold", pad=40)

# Legend
ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.05), fontsize=16, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
