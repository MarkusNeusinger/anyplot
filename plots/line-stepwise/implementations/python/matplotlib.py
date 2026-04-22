""" pyplots.ai
line-stepwise: Step Line Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Server capacity levels over monitoring period
np.random.seed(42)
hours = np.arange(0, 24, 1)  # 24 hours

# Server capacity changes at discrete intervals
# Start at baseline, with step changes at various times
capacity = np.array(
    [
        50,
        50,
        50,
        50,
        50,
        50,  # Night: low capacity
        75,
        75,
        100,
        100,
        100,
        100,  # Morning ramp-up
        150,
        150,
        150,
        125,
        125,
        100,  # Peak hours, then decline
        100,
        75,
        75,
        75,
        50,
        50,  # Evening wind-down
    ]
)

# Create plot (4800x2700 px at 300 dpi = 16x9 inches)
fig, ax = plt.subplots(figsize=(16, 9))

# Step plot with 'post' alignment - value persists until next point
ax.step(hours, capacity, where="post", linewidth=3.5, color="#306998", label="Server Capacity")

# Add markers at change points to show discrete values
ax.scatter(hours, capacity, s=120, color="#FFD43B", edgecolors="#306998", linewidths=2, zorder=5)

# Fill under the step curve for visual emphasis
ax.fill_between(hours, capacity, step="post", alpha=0.2, color="#306998")

# Labels and styling
ax.set_xlabel("Hour of Day", fontsize=20)
ax.set_ylabel("Server Capacity (units)", fontsize=20)
ax.set_title("line-stepwise · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Set axis limits with padding
ax.set_xlim(-0.5, 23.5)
ax.set_ylim(0, 175)

# Configure x-axis ticks for hours
ax.set_xticks(np.arange(0, 24, 2))
ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)])

# Grid and legend
ax.grid(True, alpha=0.3, linestyle="--")
ax.legend(fontsize=16, loc="upper right")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
