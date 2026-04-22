""" pyplots.ai
line-stepwise: Step Line Plot
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Data - Daily server load showing discrete state changes
np.random.seed(42)
hours = np.arange(0, 24)
# Simulate server load with discrete jumps at certain hours
base_load = np.array([20, 20, 15, 15, 15, 25, 40, 65, 80, 85, 85, 75, 70, 75, 80, 85, 90, 85, 70, 55, 45, 35, 30, 25])
load_noise = np.random.randint(-3, 4, size=24)
server_load = np.clip(base_load + load_noise, 10, 100)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))
sns.set_style("whitegrid")

# Step line plot using seaborn lineplot with drawstyle
# seaborn's lineplot wraps matplotlib, so we use drawstyle for step effect
sns.lineplot(x=hours, y=server_load, ax=ax, drawstyle="steps-post", linewidth=3, color="#306998")

# Add markers at each data point for clarity
sns.scatterplot(x=hours, y=server_load, ax=ax, s=150, color="#FFD43B", edgecolor="#306998", linewidth=2, zorder=5)

# Styling
ax.set_xlabel("Hour of Day", fontsize=20)
ax.set_ylabel("Server Load (%)", fontsize=20)
ax.set_title("line-stepwise · seaborn · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set axis limits
ax.set_xlim(-0.5, 23.5)
ax.set_ylim(0, 105)

# Customize grid
ax.grid(True, alpha=0.3, linestyle="--")

# Set x-ticks to show every 2 hours
ax.set_xticks(np.arange(0, 24, 2))

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
