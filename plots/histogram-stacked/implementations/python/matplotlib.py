""" pyplots.ai
histogram-stacked: Stacked Histogram
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Response times (ms) for three different server regions
np.random.seed(42)

# Generate data for three server regions with different distributions
us_east = np.random.normal(loc=45, scale=12, size=200)  # Fast region
europe = np.random.normal(loc=65, scale=15, size=180)  # Medium region
asia = np.random.normal(loc=80, scale=20, size=150)  # Slower region

# Clip to realistic values
us_east = np.clip(us_east, 10, 120)
europe = np.clip(europe, 15, 140)
asia = np.clip(asia, 20, 160)

# Colors - Python Blue first, then Yellow, then complementary
colors = ["#306998", "#FFD43B", "#5BA85B"]
labels = ["US-East", "Europe", "Asia-Pacific"]

# Create plot (4800x2700 px at 300 DPI = 16x9 inches)
fig, ax = plt.subplots(figsize=(16, 9))

# Create stacked histogram
ax.hist(
    [us_east, europe, asia],
    bins=20,
    stacked=True,
    color=colors,
    label=labels,
    edgecolor="white",
    linewidth=0.8,
    alpha=0.9,
)

# Labels and styling (scaled font sizes for 4800x2700)
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Number of Requests", fontsize=20)
ax.set_title("histogram-stacked · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Legend
ax.legend(fontsize=16, loc="upper right", framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
