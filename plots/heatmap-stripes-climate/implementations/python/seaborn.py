"""anyplot.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 92/100 | Updated: 2026-06-02
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: blue = cold and red = warm are positions 3 and 5
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLD, WARM = IMPRINT_PALETTE[2], IMPRINT_PALETTE[4]

# Imprint diverging colormap, cold to warm. The dark midpoint is a mid grey so that
# near-zero stripes stay visible against the dark page.
MIDPOINT = "#FAF8F1" if THEME == "light" else "#A8A79F"
imprint_div = LinearSegmentedColormap.from_list("imprint_div", [COLD, MIDPOINT, WARM])

# Columns: set these to your table's column names
YEAR = "Year"  # role: year
ANOMALY = "Temperature anomaly (°C)"  # role: anomaly

# Data: replace this block with your own table, for example df = pd.read_csv("anomalies.csv")
np.random.seed(42)
years = np.arange(1850, 2025)
baseline_trend = np.concatenate(
    [
        np.linspace(-0.3, -0.2, 60),
        np.linspace(-0.2, -0.1, 40),
        np.linspace(-0.1, 0.1, 30),
        np.linspace(0.1, 0.5, 25),
        np.linspace(0.5, 1.3, 20),
    ]
)
df = pd.DataFrame({YEAR: years, ANOMALY: baseline_trend + np.random.normal(0, 0.12, len(years))})

# Plot
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

anomaly_matrix = df[ANOMALY].to_numpy().reshape(1, -1)
vmax = np.nanmax(np.abs(anomaly_matrix))

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

# Pure stripe visualization: no axes, labels or gridlines
ax.set_axis_off()
# Band about 3:1: 0.98 x 3200 px wide, 0.64 x 1800 px tall
ax.set_position([0.01, 0.17, 0.98, 0.64])

# Title
title = "heatmap-stripes-climate · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(round(12 * ratio), 8)
fig.text(0.5, 0.89, title, ha="center", va="center", fontsize=title_fontsize, fontweight="medium", color=INK)

# Year markers below the stripe band
fig.text(0.015, 0.09, str(df[YEAR].iloc[0]), fontsize=10, color=INK_SOFT, ha="left")
fig.text(0.985, 0.09, str(df[YEAR].iloc[-1]), fontsize=10, color=INK_SOFT, ha="right")

# Save: no bbox_inches="tight", to keep the exact 3200x1800 canvas
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
