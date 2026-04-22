""" pyplots.ai
line-filled: Filled Line Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Daily website traffic over 60 days
np.random.seed(42)
days = np.arange(60)
# Simulate website traffic with trend and weekly pattern
base_traffic = 5000 + days * 50  # Upward trend
weekly_pattern = 800 * np.sin(2 * np.pi * days / 7)  # Weekly cycle
noise = np.random.normal(0, 300, size=60)
visitors = base_traffic + weekly_pattern + noise
visitors = np.maximum(visitors, 0)  # Ensure non-negative

# Create plot (4800x2700 px)
fig, ax = plt.subplots(figsize=(16, 9))

# Use seaborn's lineplot for the line
sns.lineplot(x=days, y=visitors, ax=ax, color="#306998", linewidth=3, label="Daily Visitors")

# Fill the area under the curve
ax.fill_between(days, visitors, alpha=0.4, color="#306998")

# Labels and styling
ax.set_xlabel("Day", fontsize=20)
ax.set_ylabel("Website Visitors", fontsize=20)
ax.set_title("line-filled · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper left")

# Set y-axis to start at 0 for proper area visualization
ax.set_ylim(bottom=0)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
