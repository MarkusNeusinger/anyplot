""" pyplots.ai
bar-stacked: Stacked Bar Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-26
"""

import matplotlib.pyplot as plt
import numpy as np


# Seed for reproducibility (data is deterministic but seed documents intent)
np.random.seed(42)

# Data: Quarterly revenue by product category (in millions USD)
categories = ["Q1", "Q2", "Q3", "Q4"]
products = ["Software", "Hardware", "Services", "Support"]

# Revenue data showing realistic business patterns
software = np.array([45, 52, 48, 68])  # Growing, spike in Q4
hardware = np.array([32, 28, 35, 42])  # Variable with Q4 boost
services = np.array([28, 31, 38, 35])  # Steady growth
support = np.array([15, 18, 20, 22])  # Consistent increase

# Colors: Python blue primary, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#4ECDC4", "#FF6B6B"]

# Create figure (4800 x 2700 px at 300 dpi = 16 x 9 inches)
fig, ax = plt.subplots(figsize=(16, 9))

# Calculate bar positions
x = np.arange(len(categories))
bar_width = 0.6

# Create stacked bars
bottom = np.zeros(len(categories))
for i, (product, values) in enumerate(zip(products, [software, hardware, services, support], strict=True)):
    ax.bar(x, values, bar_width, label=product, bottom=bottom, color=colors[i], edgecolor="white", linewidth=1.5)
    bottom += values

# Add total labels above each stacked bar
totals = software + hardware + services + support
for i, total in enumerate(totals):
    ax.text(i, total + 3, f"${total}M", ha="center", va="bottom", fontsize=18, fontweight="bold", color="#333333")

# Styling
ax.set_xlabel("Quarter", fontsize=20)
ax.set_ylabel("Revenue (Millions USD)", fontsize=20)
ax.set_title("bar-stacked · matplotlib · pyplots.ai", fontsize=24)
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.tick_params(axis="both", labelsize=16)

# Legend (outside plot area to avoid overlap with data)
ax.legend(fontsize=16, loc="upper left", bbox_to_anchor=(1.02, 1), framealpha=0.95)

# Grid (subtle, horizontal only for bar charts)
ax.yaxis.grid(True, alpha=0.3, linestyle="--")
ax.set_axisbelow(True)

# Clean up spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Set y-axis to start at 0 and add headroom for labels
ax.set_ylim(0, max(totals) + 20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
