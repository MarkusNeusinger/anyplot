""" pyplots.ai
radar-multi: Multi-Series Radar Chart
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set seaborn style
sns.set_style("whitegrid")
sns.set_context("talk", font_scale=1.2)

# Data - Product comparison across quality dimensions
categories = ["Performance", "Reliability", "Usability", "Features", "Support", "Value"]
n_categories = len(categories)

# Three products being compared (0-100 scale)
np.random.seed(42)
products = {
    "Product A": [85, 90, 75, 80, 70, 85],
    "Product B": [70, 75, 90, 85, 80, 70],
    "Product C": [80, 65, 85, 70, 90, 75],
}

# Colors using Python Blue first, then complementary colors
colors = ["#306998", "#FFD43B", "#E74C3C"]

# Calculate angles for each axis
angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False).tolist()
angles += angles[:1]  # Close the polygon

# Create figure with polar subplot (square format for radar)
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"projection": "polar"})

# Plot each product series
for idx, (product_name, values) in enumerate(products.items()):
    values_closed = values + values[:1]  # Close the polygon

    # Fill with transparency
    ax.fill(angles, values_closed, alpha=0.25, color=colors[idx], label=product_name)

    # Outline with larger markers
    ax.plot(angles, values_closed, "o-", linewidth=3, markersize=10, color=colors[idx])

# Set category labels on each axis
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=18)

# Set radial ticks and limits
ax.set_ylim(0, 100)
ax.set_yticks([20, 40, 60, 80, 100])
ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=14, color="gray")

# Style gridlines
ax.yaxis.grid(True, linestyle="--", alpha=0.4)
ax.xaxis.grid(True, linestyle="-", alpha=0.3)

# Add title
ax.set_title("radar-multi · seaborn · pyplots.ai", fontsize=24, pad=30, fontweight="bold")

# Add legend
ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1.1), fontsize=16, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
