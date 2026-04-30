""" anyplot.ai
ridgeline-basic: Basic Ridgeline Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 89/100 | Updated: 2026-04-30
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - Monthly temperature distributions (Northern Hemisphere)
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

base_temps = [2, 4, 8, 14, 18, 22, 25, 24, 20, 14, 8, 4]
data = {}
for i, month in enumerate(months):
    variation = 4 if i in [3, 4, 9, 10] else 3
    data[month] = np.random.normal(base_temps[i], variation, 150)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

x_range = np.linspace(-10, 40, 500)
overlap = 0.6
scale = 2.5

colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(months)))

for i, month in enumerate(reversed(months)):
    y_offset = i * (1 - overlap)
    values = data[month]

    kde = stats.gaussian_kde(values)
    density = kde(x_range) * scale

    ax.fill_between(
        x_range,
        y_offset,
        y_offset + density,
        alpha=0.8,
        color=colors[len(months) - 1 - i],
        edgecolor=PAGE_BG,
        linewidth=1.5,
    )
    ax.plot(x_range, [y_offset] * len(x_range), color=INK_SOFT, linewidth=0.5, alpha=0.3)

# Y-ticks
y_positions = [(len(months) - 1 - i) * (1 - overlap) for i in range(len(months))]
ax.set_yticks(y_positions)
ax.set_yticklabels(months, fontsize=16, color=INK_SOFT)

# Style
ax.set_xlabel("Temperature (°C)", fontsize=20, color=INK)
ax.set_title("ridgeline-basic · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="x", labelsize=16, colors=INK_SOFT)
ax.set_xlim(-10, 40)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_color(INK_SOFT)

ax.grid(True, axis="x", alpha=0.15, color=INK)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
