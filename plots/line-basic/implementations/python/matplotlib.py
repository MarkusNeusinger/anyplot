""" pyplots.ai
line-basic: Basic Line Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Monthly temperature readings over a year
np.random.seed(42)
months = np.arange(1, 13)
# Simulate temperature pattern (warmer in summer, cooler in winter)
base_temp = 15 + 12 * np.sin((months - 4) * np.pi / 6)
temperature = base_temp + np.random.randn(12) * 1.5

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

ax.plot(
    months,
    temperature,
    linewidth=3,
    color="#306998",
    marker="o",
    markersize=10,
    markerfacecolor="#FFD43B",
    markeredgecolor="#306998",
    markeredgewidth=2,
)

# Labels and styling (scaled font sizes for 4800x2700)
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Temperature (°C)", fontsize=20)
ax.set_title("line-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set x-axis ticks to show all months
ax.set_xticks(months)
ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])

# Grid for readability
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
