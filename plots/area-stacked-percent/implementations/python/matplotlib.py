""" pyplots.ai
area-stacked-percent: 100% Stacked Area Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Market share evolution over time
np.random.seed(42)
years = np.arange(2015, 2025)

# Create realistic market share data with different trends
company_a = np.array([45, 43, 40, 38, 35, 33, 30, 28, 26, 24])  # Declining leader
company_b = np.array([30, 32, 34, 35, 36, 37, 38, 39, 40, 41])  # Growing challenger
company_c = np.array([15, 16, 17, 18, 19, 20, 21, 22, 23, 24])  # Steady growth
company_d = np.array([10, 9, 9, 9, 10, 10, 11, 11, 11, 11])  # Stable small player

# Stack the data
data = np.vstack([company_a, company_b, company_c, company_d])

# Normalize to 100%
totals = data.sum(axis=0)
data_percent = data / totals * 100

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Define colors (Python Blue, Yellow, and complementary colors)
colors = ["#306998", "#FFD43B", "#4B8BBE", "#FFE873"]
labels = ["Company A", "Company B", "Company C", "Company D"]

# Create stacked area chart
ax.stackplot(years, data_percent, labels=labels, colors=colors, alpha=0.85, edgecolor="white", linewidth=1.5)

# Styling
ax.set_xlabel("Year", fontsize=20)
ax.set_ylabel("Market Share (%)", fontsize=20)
ax.set_title("area-stacked-percent · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set axis limits
ax.set_xlim(years[0], years[-1])
ax.set_ylim(0, 100)

# Y-axis ticks
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])

# X-axis ticks (show all years)
ax.set_xticks(years)

# Grid
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Legend
ax.legend(loc="upper right", fontsize=16, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
