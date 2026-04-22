""" pyplots.ai
ridgeline-basic: Basic Ridgeline Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Monthly temperature distributions (12 months)
np.random.seed(42)

months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# Generate realistic temperature distributions for each month (Northern Hemisphere pattern)
base_temps = [2, 4, 8, 14, 18, 22, 25, 24, 20, 14, 8, 4]
data = {}
for i, month in enumerate(months):
    # More variation in spring/fall, less in summer/winter
    variation = 4 if i in [3, 4, 9, 10] else 3
    data[month] = np.random.normal(base_temps[i], variation, 150)

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Settings for ridgeline display
x_range = np.linspace(-10, 40, 500)
overlap = 0.6  # 60% overlap between ridges
scale = 2.5  # Scale factor for density curves

# Color gradient using viridis colormap
colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(months)))

# Plot ridges from bottom to top (reverse order so January is at top)
for i, month in enumerate(reversed(months)):
    y_offset = i * (1 - overlap)
    values = data[month]

    # Gaussian KDE: Scott's rule for bandwidth, then sum Gaussians
    n = len(values)
    bandwidth = 1.06 * np.std(values) * n ** (-1 / 5)
    density = np.sum([np.exp(-0.5 * ((x_range - v) / bandwidth) ** 2) for v in values], axis=0)
    density /= n * bandwidth * np.sqrt(2 * np.pi)
    density *= scale

    # Fill the ridge
    ax.fill_between(
        x_range,
        y_offset,
        y_offset + density,
        alpha=0.8,
        color=colors[len(months) - 1 - i],
        edgecolor="white",
        linewidth=1.5,
    )

    # Add baseline
    ax.plot(x_range, [y_offset] * len(x_range), color="white", linewidth=0.5, alpha=0.5)

# Set y-ticks at ridge positions
y_positions = [(len(months) - 1 - i) * (1 - overlap) for i in range(len(months))]
ax.set_yticks(y_positions)
ax.set_yticklabels(months, fontsize=14)

# Styling
ax.set_xlabel("Temperature (°C)", fontsize=20)
ax.set_title("ridgeline-basic · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="x", labelsize=16)
ax.set_xlim(-10, 40)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

# Subtle grid on x-axis only
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
