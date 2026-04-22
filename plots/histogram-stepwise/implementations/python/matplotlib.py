""" pyplots.ai
histogram-stepwise: Step Histogram
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Two distributions for comparison
np.random.seed(42)
morning_temps = np.random.normal(loc=15, scale=3, size=200)  # Morning temperatures (°C)
afternoon_temps = np.random.normal(loc=22, scale=4, size=200)  # Afternoon temperatures (°C)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Step histograms (outline only, no fill)
ax.hist(morning_temps, bins=25, histtype="step", linewidth=3, color="#306998", label="Morning")
ax.hist(afternoon_temps, bins=25, histtype="step", linewidth=3, color="#FFD43B", label="Afternoon")

# Labels and styling
ax.set_xlabel("Temperature (°C)", fontsize=20)
ax.set_ylabel("Frequency", fontsize=20)
ax.set_title("histogram-stepwise · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.legend(fontsize=16, loc="upper right")
ax.grid(True, alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
