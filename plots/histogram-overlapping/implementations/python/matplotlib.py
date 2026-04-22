""" pyplots.ai
histogram-overlapping: Overlapping Histograms
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-25
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Comparing salary distributions across three departments
np.random.seed(42)

# Engineering: higher salaries, tighter distribution
engineering = np.random.normal(95000, 12000, 200)

# Marketing: moderate salaries, wider spread
marketing = np.random.normal(75000, 18000, 180)

# Sales: lower base but high variance due to commissions
sales = np.random.normal(65000, 22000, 220)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Define consistent bins for all groups
bins = np.linspace(20000, 150000, 35)

# Plot overlapping histograms with transparency
ax.hist(engineering, bins=bins, alpha=0.5, label="Engineering", color="#306998", edgecolor="#1e4460", linewidth=1.5)
ax.hist(marketing, bins=bins, alpha=0.5, label="Marketing", color="#FFD43B", edgecolor="#b89500", linewidth=1.5)
ax.hist(sales, bins=bins, alpha=0.5, label="Sales", color="#4ECDC4", edgecolor="#2a7a74", linewidth=1.5)

# Labels and styling
ax.set_xlabel("Annual Salary ($)", fontsize=20)
ax.set_ylabel("Number of Employees", fontsize=20)
ax.set_title("histogram-overlapping · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper right")
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Format x-axis with thousands separator
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x / 1000:.0f}k"))

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
