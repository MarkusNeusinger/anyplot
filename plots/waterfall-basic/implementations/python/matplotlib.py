""" pyplots.ai
waterfall-basic: Basic Waterfall Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Quarterly financial breakdown from revenue to net income
categories = ["Revenue", "Cost of Goods", "Gross Profit", "Operating Expenses", "Other Income", "Taxes", "Net Income"]
# Values: First and last are totals, middle values are changes (None = calculated totals)
values = [500, -200, None, -150, 25, -45, None]

# Calculate running totals and determine actual bar values
n = len(categories)
running_total = np.zeros(n)
bar_values = np.zeros(n)
bar_bottom = np.zeros(n)

running_total[0] = values[0]  # Starting value
bar_values[0] = values[0]
bar_bottom[0] = 0

current = values[0]
for i in range(1, n):
    if values[i] is None:
        # This is a subtotal bar (Gross Profit or Net Income)
        running_total[i] = current
        bar_values[i] = current
        bar_bottom[i] = 0
    else:
        # This is a change bar
        running_total[i] = current + values[i]
        bar_values[i] = values[i]
        if values[i] >= 0:
            bar_bottom[i] = current
        else:
            bar_bottom[i] = current + values[i]
        current = running_total[i]

# Determine colors: blue for totals, green for positive, red for negative
colors = []
for val in values:
    if val is None:
        colors.append("#306998")  # Python Blue for totals
    elif val >= 0:
        colors.append("#4CAF50")  # Green for positive
    else:
        colors.append("#E53935")  # Red for negative

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

x = np.arange(n)
bar_width = 0.6

# Draw bars
bars = ax.bar(x, np.abs(bar_values), width=bar_width, bottom=bar_bottom, color=colors, edgecolor="white", linewidth=2)

# Draw connecting lines between bars
for i in range(n - 1):
    ax.plot(
        [x[i] + bar_width / 2, x[i + 1] - bar_width / 2],
        [running_total[i], running_total[i]],
        color="#666666",
        linestyle="--",
        linewidth=2,
        zorder=1,
    )

# Add value labels on bars
for i, bar in enumerate(bars):
    height = bar.get_height()
    y_pos = bar_bottom[i] + height / 2

    # Format label
    if values[i] is None or values[i] >= 0:
        label = f"${int(bar_values[i])}"
    else:
        label = f"-${int(abs(bar_values[i]))}"

    ax.text(
        bar.get_x() + bar.get_width() / 2,
        y_pos,
        label,
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color="white",
    )

# Styling
ax.set_xlabel("Category", fontsize=20)
ax.set_ylabel("Amount ($)", fontsize=20)
ax.set_title("waterfall-basic · matplotlib · pyplots.ai", fontsize=24)
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=16, rotation=15, ha="right")
ax.tick_params(axis="y", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Set y-axis to start from 0
ax.set_ylim(bottom=0)

# Add a subtle baseline
ax.axhline(y=0, color="black", linewidth=1)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
