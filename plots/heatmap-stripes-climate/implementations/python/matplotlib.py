""" anyplot.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 87/100 | Updated: 2026-06-02
"""

import os

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Data - synthetic global temperature anomalies (1850-2024) relative to 1961-1990 baseline
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

# Imprint diverging colormap reversed: blue (cold) -> warm-neutral -> red (warm)
# Visible neutral midpoint keeps near-zero anomaly stripes distinguishable from background
midpoint = "#D4CFC6" if THEME == "light" else "#4A4844"
imprint_div_r = LinearSegmentedColormap.from_list("imprint_div_r", ["#4467A3", midpoint, "#AE3030"])

# Plot - landscape 3200x1800 canvas (figsize=(8, 4.5) at dpi=400)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Position stripes at ~3:1 aspect ratio (3072x1026 px), close to bottom to fill canvas
ax.set_position([0.02, 0.04, 0.96, 0.57])

vmax = max(abs(anomalies.min()), abs(anomalies.max()))
norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

stripe_data = anomalies.reshape(1, -1)
ax.imshow(
    stripe_data,
    aspect="auto",
    cmap=imprint_div_r,
    norm=norm,
    extent=[years[0] - 0.5, years[-1] + 0.5, 0, 1],
    interpolation="nearest",
)

# Style - minimal: no axes, no labels, no ticks, no gridlines per spec
ax.axis("off")

# Title with path effects for subtle depth — theme-adaptive
title_str = "heatmap-stripes-climate · python · matplotlib · anyplot.ai"
title_obj = fig.text(0.5, 0.86, title_str, fontsize=12, fontweight="medium", color=INK, ha="center", va="center")
title_obj.set_path_effects([pe.withStroke(linewidth=3, foreground=PAGE_BG)])

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
