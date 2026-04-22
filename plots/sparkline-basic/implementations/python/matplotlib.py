""" pyplots.ai
sparkline-basic: Basic Sparkline
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - simulate daily website traffic with realistic trend patterns
np.random.seed(42)
n_points = 50
# Base trend with weekly seasonality and some noise
trend = np.linspace(100, 150, n_points)  # Gradual growth
weekly_pattern = 15 * np.sin(np.linspace(0, 4 * np.pi, n_points))  # Weekly cycles
noise = np.random.randn(n_points) * 8
values = trend + weekly_pattern + noise

# Create figure - sparklines are wide and short (6:1 aspect ratio)
# Using 16:2.67 to maintain 4800x2700 equivalent quality at high dpi
fig, ax = plt.subplots(figsize=(16, 2.67))

# Plot the sparkline - minimal, clean line
ax.plot(range(len(values)), values, linewidth=2.5, color="#306998", solid_capstyle="round")

# Highlight min and max points
min_idx = np.argmin(values)
max_idx = np.argmax(values)
ax.scatter([min_idx], [values[min_idx]], s=150, color="#d62728", zorder=5, edgecolors="white", linewidths=2)
ax.scatter([max_idx], [values[max_idx]], s=150, color="#2ca02c", zorder=5, edgecolors="white", linewidths=2)

# Highlight first and last points
ax.scatter([0], [values[0]], s=120, color="#306998", zorder=5, edgecolors="white", linewidths=2)
ax.scatter([len(values) - 1], [values[-1]], s=120, color="#FFD43B", zorder=5, edgecolors="white", linewidths=2)

# Remove all axes and chart chrome - pure sparkline aesthetic
ax.set_xticks([])
ax.set_yticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["left"].set_visible(False)

# Add subtle padding around the line
y_margin = (values.max() - values.min()) * 0.15
ax.set_ylim(values.min() - y_margin, values.max() + y_margin)
ax.set_xlim(-1, len(values))

# Title at the bottom right corner - sparkline style
ax.text(
    0.99,
    0.02,
    "sparkline-basic · matplotlib · pyplots.ai",
    transform=ax.transAxes,
    fontsize=14,
    color="#666666",
    ha="right",
    va="bottom",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")
