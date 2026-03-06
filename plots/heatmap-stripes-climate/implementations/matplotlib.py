""" pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-06
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm


# Data - Synthetic global temperature anomalies (1850-2024) relative to 1961-1990 baseline
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

base_trend = np.piecewise(
    years.astype(float),
    [years < 1910, (years >= 1910) & (years < 1945), (years >= 1945) & (years < 1975), years >= 1975],
    [
        lambda y: -0.3 + (y - 1850) * 0.002,
        lambda y: -0.2 + (y - 1910) * 0.008,
        lambda y: 0.0 + (y - 1945) * 0.001,
        lambda y: 0.03 + (y - 1975) * 0.02,
    ],
)
noise = np.random.normal(0, 0.08, n_years)
anomalies = base_trend + noise

# Custom colormap matching spec: deep blue (#08306b) → white → deep red (#67000d)
cmap = LinearSegmentedColormap.from_list(
    "climate_stripes",
    ["#08306b", "#2171b5", "#6baed6", "#c6dbef", "#ffffff", "#fcbba1", "#fb6a4a", "#cb181d", "#67000d"],
)

# Plot - standard 4800x2700 canvas (16x9 at 300dpi)
fig, ax = plt.subplots(figsize=(16, 9))

# Position stripes with ~3:1 aspect ratio within the canvas
ax.set_position([0.03, 0.05, 0.94, 0.82])

vmax = max(abs(anomalies.min()), abs(anomalies.max()))
norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

# Use imshow for efficient stripe rendering - reshape anomalies as single-row image
stripe_data = anomalies.reshape(1, -1)
ax.imshow(
    stripe_data,
    aspect="auto",
    cmap=cmap,
    norm=norm,
    extent=[years[0] - 0.5, years[-1] + 0.5, 0, 1],
    interpolation="nearest",
)

# Style - Minimal: no axes, no labels, no ticks, no gridlines
ax.axis("off")

ax.set_title("heatmap-stripes-climate · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=20)

plt.savefig("plot.png", dpi=300)
