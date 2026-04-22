""" pyplots.ai
density-rug: Density Plot with Rug Marks
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde


# Data - Response times (ms) for a web service with bimodal distribution
np.random.seed(42)
# Mix of fast responses (cache hits) and slower responses (database queries)
fast_responses = np.random.normal(loc=45, scale=8, size=80)
slow_responses = np.random.normal(loc=120, scale=25, size=70)
response_times = np.concatenate([fast_responses, slow_responses])
response_times = response_times[response_times > 0]  # Keep only positive values

# Compute KDE
kde = gaussian_kde(response_times, bw_method="scott")
x_range = np.linspace(response_times.min() - 10, response_times.max() + 10, 500)
density = kde(x_range)

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# KDE curve with fill
ax.fill_between(x_range, density, alpha=0.4, color="#306998", label="KDE Density")
ax.plot(x_range, density, color="#306998", linewidth=3)

# Rug marks along x-axis
rug_height = 0.015 * density.max()  # Height relative to density
for val in response_times:
    ax.plot([val, val], [0, rug_height], color="#306998", alpha=0.6, linewidth=2)

# Add a horizontal line at y=0 for visual clarity
ax.axhline(y=0, color="black", linewidth=0.5)

# Labels and styling
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Density", fontsize=20)
ax.set_title("density-rug · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Set y-axis to start at 0 with some padding at top
ax.set_ylim(bottom=-0.0005, top=density.max() * 1.1)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
