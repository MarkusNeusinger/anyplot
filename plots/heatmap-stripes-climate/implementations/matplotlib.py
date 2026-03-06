""" pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-06
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm


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

# Plot
fig, ax = plt.subplots(figsize=(16, 5))

vmax = max(abs(anomalies.min()), abs(anomalies.max()))
norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
cmap = plt.get_cmap("RdBu_r")

colors = cmap(norm(anomalies))
ax.bar(years, 1, width=1.0, bottom=0, color=colors, edgecolor="none")

# Style - Minimal: no axes, no labels, no ticks, no gridlines
ax.set_xlim(years[0] - 0.5, years[-1] + 0.5)
ax.set_ylim(0, 1)
ax.axis("off")

ax.set_title("heatmap-stripes-climate · matplotlib · pyplots.ai", fontsize=20, fontweight="medium", pad=12)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
