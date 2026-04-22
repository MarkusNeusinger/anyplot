""" pyplots.ai
box-notched: Notched Box Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Employee performance scores across departments
np.random.seed(42)

# Create realistic data with different distributions to showcase notch comparison
# Engineering: Higher scores, tight distribution
engineering = np.random.normal(loc=82, scale=8, size=60)
engineering = np.clip(engineering, 50, 100)

# Sales: Medium scores, wider spread
sales = np.random.normal(loc=75, scale=12, size=55)
sales = np.clip(sales, 40, 100)

# Marketing: Similar to sales (overlapping notches expected)
marketing = np.random.normal(loc=73, scale=10, size=50)
marketing = np.clip(marketing, 45, 100)

# Support: Lower scores with some outliers
support_base = np.random.normal(loc=68, scale=9, size=45)
support_outliers = np.array([95, 98, 35, 32])  # Add explicit outliers
support = np.concatenate([support_base, support_outliers])
support = np.clip(support, 25, 100)

# HR: Moderate scores
hr = np.random.normal(loc=78, scale=7, size=40)
hr = np.clip(hr, 55, 100)

data = [engineering, sales, marketing, support, hr]
departments = ["Engineering", "Sales", "Marketing", "Support", "HR"]

# Colors - Python Blue as primary, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#4ECDC4", "#FF6B6B", "#95E1A3"]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Create notched boxplot
bp = ax.boxplot(
    data,
    notch=True,  # Enable notches for median confidence interval
    patch_artist=True,  # Enable filling boxes with color
    tick_labels=departments,
    widths=0.6,
    showfliers=True,  # Show outliers
    flierprops={"marker": "o", "markerfacecolor": "#666666", "markersize": 10, "alpha": 0.7},
    medianprops={"color": "#333333", "linewidth": 2.5},
    whiskerprops={"color": "#666666", "linewidth": 2},
    capprops={"color": "#666666", "linewidth": 2},
)

# Apply colors to boxes
for patch, color in zip(bp["boxes"], colors, strict=True):
    patch.set_facecolor(color)
    patch.set_alpha(0.75)
    patch.set_edgecolor("#333333")
    patch.set_linewidth(2)

# Labels and styling
ax.set_xlabel("Department", fontsize=20)
ax.set_ylabel("Performance Score", fontsize=20)
ax.set_title("box-notched · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, axis="y", alpha=0.3, linestyle="--")

# Add annotation explaining notches
ax.annotate(
    "Non-overlapping notches suggest\nsignificant difference in medians",
    xy=(1, 82),
    xytext=(1.5, 92),
    fontsize=14,
    arrowprops={"arrowstyle": "->", "color": "#666666", "lw": 1.5},
    bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
