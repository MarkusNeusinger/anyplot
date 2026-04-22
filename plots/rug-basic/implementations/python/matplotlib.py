""" pyplots.ai
rug-basic: Basic Rug Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - trimodal distribution to show clustering patterns and gaps
np.random.seed(42)
values = np.concatenate(
    [
        np.random.normal(25, 4, 50),  # Tight cluster around 25
        np.random.normal(55, 7, 35),  # Wider cluster around 55
        np.random.normal(75, 3, 15),  # Small cluster at high end
    ]
)

# Create plot (4800x2700 px at 300 dpi = 16x9 inches)
fig, ax = plt.subplots(figsize=(16, 9))

# Rug plot - vertical tick marks along x-axis showing every data point
# Each tick shows the exact position of one observation
ax.vlines(values, ymin=0, ymax=0.7, color="#306998", alpha=0.7, linewidth=3)

# Set axis limits - keep plot in lower portion of canvas
ax.set_xlim(5, 90)
ax.set_ylim(0, 1)

# Hide y-axis since rug plots focus on x-distribution only
ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Labels and styling
ax.set_xlabel("Measurement Value", fontsize=20)
ax.set_title("rug-basic · matplotlib · pyplots.ai", fontsize=24, pad=20)
ax.tick_params(axis="x", labelsize=16)

# Add text annotations above clusters to explain the data
ax.text(25, 0.85, "Dense cluster\n(n=50)", ha="center", fontsize=16, color="#306998")
ax.text(55, 0.85, "Wider spread\n(n=35)", ha="center", fontsize=16, color="#306998")
ax.text(75, 0.85, "Small group\n(n=15)", ha="center", fontsize=16, color="#306998")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
