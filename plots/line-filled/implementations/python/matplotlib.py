""" pyplots.ai
line-filled: Filled Line Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data: Monthly website traffic over a year
np.random.seed(42)
months = np.arange(1, 13)
# Simulate website traffic with seasonal trend (higher in summer)
base_traffic = 50000
seasonal = 15000 * np.sin((months - 3) * np.pi / 6)  # Peak in summer
noise = np.random.normal(0, 3000, 12)
traffic = base_traffic + seasonal + noise
traffic = np.maximum(traffic, 0)  # Ensure non-negative

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

# Fill the area under the line
ax.fill_between(months, traffic, alpha=0.4, color="#306998")

# Draw the line on top
ax.plot(months, traffic, linewidth=3, color="#306998")

# Styling
ax.set_xlabel("Month", fontsize=20)
ax.set_ylabel("Website Visitors", fontsize=20)
ax.set_title("line-filled · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.set_xticks(months)
ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
ax.set_xlim(1, 12)
ax.set_ylim(0, None)  # Start y-axis at 0 for proper fill effect
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
