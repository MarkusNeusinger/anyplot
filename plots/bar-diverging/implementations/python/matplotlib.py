""" pyplots.ai
bar-diverging: Diverging Bar Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 97/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


# Data - Product satisfaction survey scores (-100 to +100)
categories = [
    "Customer Support",
    "Product Quality",
    "Pricing",
    "Website Experience",
    "Delivery Speed",
    "Return Policy",
    "Mobile App",
    "Product Range",
    "Payment Options",
    "Brand Trust",
    "Sustainability",
    "Loyalty Program",
]

# Net satisfaction scores (positive = satisfied, negative = dissatisfied)
np.random.seed(42)
values = np.array([45, 72, -38, 28, -15, 55, -52, 33, 61, 85, -8, 18])

# Sort by value for better pattern recognition
sorted_indices = np.argsort(values)
categories_sorted = [categories[i] for i in sorted_indices]
values_sorted = values[sorted_indices]

# Create colors based on positive/negative values
colors = ["#306998" if v >= 0 else "#FFD43B" for v in values_sorted]

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Create horizontal bars
y_pos = np.arange(len(categories_sorted))
ax.barh(y_pos, values_sorted, color=colors, height=0.7, edgecolor="white", linewidth=1)

# Add vertical line at zero
ax.axvline(x=0, color="#333333", linewidth=2)

# Styling
ax.set_yticks(y_pos)
ax.set_yticklabels(categories_sorted, fontsize=16)
ax.set_xlabel("Net Satisfaction Score", fontsize=20)
ax.set_title("bar-diverging · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="x", labelsize=16)

# Grid on x-axis only, subtle
ax.xaxis.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Add value labels at the end of each bar
for val, y in zip(values_sorted, y_pos, strict=True):
    offset = 3 if val >= 0 else -3
    ha = "left" if val >= 0 else "right"
    ax.text(val + offset, y, f"{val:+d}", va="center", ha=ha, fontsize=14, fontweight="bold")

# Set x-axis limits with padding
max_abs = max(abs(values_sorted.min()), abs(values_sorted.max()))
ax.set_xlim(-max_abs - 20, max_abs + 20)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Add legend
legend_elements = [
    Patch(facecolor="#306998", edgecolor="white", label="Positive (Satisfied)"),
    Patch(facecolor="#FFD43B", edgecolor="white", label="Negative (Dissatisfied)"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=16, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
