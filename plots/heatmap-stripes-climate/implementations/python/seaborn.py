""" anyplot.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-06-02
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint diverging colormap — blue=cold, red=warm (reversed imprint_div for semantic clarity)
# Use INK_MUTED (#A8A79F) as dark midpoint so near-zero stripes stay visible against dark bg
midpoint = "#FAF8F1" if THEME == "light" else "#A8A79F"
imprint_div = LinearSegmentedColormap.from_list("imprint_div", ["#4467A3", midpoint, "#AE3030"])

# Data
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

baseline_trend = np.concatenate(
    [
        np.linspace(-0.3, -0.2, 60),
        np.linspace(-0.2, -0.1, 40),
        np.linspace(-0.1, 0.1, 30),
        np.linspace(0.1, 0.5, 25),
        np.linspace(0.5, 1.3, 20),
    ]
)
noise = np.random.normal(0, 0.12, n_years)
anomalies = baseline_trend + noise
anomaly_matrix = anomalies.reshape(1, -1)

# Plot — landscape 3200×1800 px (stripes need wide format per spec)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

vmax = max(abs(anomalies.min()), abs(anomalies.max()))

sns.heatmap(
    anomaly_matrix,
    ax=ax,
    cmap=imprint_div,
    center=0,
    vmin=-vmax,
    vmax=vmax,
    cbar=False,
    xticklabels=False,
    yticklabels=False,
    square=False,
    linewidths=0,
    linecolor="none",
)

# Style — pure stripe visualization: no axes, no labels, no gridlines per spec
ax.set_axis_off()
# 3:1 aspect ratio per spec: 0.98×3200=3136 px wide, 0.60×1800=1080 px tall → 2.9:1
ax.set_position([0.01, 0.15, 0.98, 0.60])

# Title
title = "heatmap-stripes-climate · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(round(12 * ratio), 8)
fig.text(0.5, 0.88, title, ha="center", va="center", fontsize=title_fontsize, fontweight="medium", color=INK)

# Year markers — larger for readability, anchored below the stripe band
fig.text(0.015, 0.07, str(years[0]), fontsize=10, color=INK_SOFT, ha="left")
fig.text(0.985, 0.07, str(years[-1]), fontsize=10, color=INK_SOFT, ha="right")

# Save — no bbox_inches='tight' to preserve exact 3200×1800 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
