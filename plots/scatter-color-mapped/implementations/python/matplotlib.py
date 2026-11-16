"""anyplot.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-08
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (the sequential map below uses positions 1 and 3)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]])

# Columns: set these to your table's column names
LATITUDE = "Latitude (°N)"  # role: x
LONGITUDE = "Longitude (°E)"  # role: y
WIND_SPEED = "Wind speed (m/s)"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("stations.csv")
np.random.seed(42)
df = pd.DataFrame(
    {
        LATITUDE: np.concatenate(
            [
                np.random.normal(40, 3, 50),
                np.random.normal(25, 4, 50),
                np.random.normal(35, 2, 50),
                np.random.normal(45, 5, 30),
            ]
        ),
        LONGITUDE: np.concatenate(
            [
                np.random.normal(-95, 4, 50),
                np.random.normal(-75, 3, 50),
                np.random.normal(-110, 5, 50),
                np.random.normal(-85, 6, 30),
            ]
        ),
        WIND_SPEED: np.concatenate(
            [
                np.random.uniform(12, 22, 50),
                np.random.uniform(8, 16, 50),
                np.random.uniform(5, 14, 50),
                np.random.uniform(10, 25, 30),
            ]
        ),
    }
)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

points = ax.scatter(
    df[LATITUDE],
    df[LONGITUDE],
    c=df[WIND_SPEED],
    cmap=imprint_seq,
    s=90,
    alpha=0.85,
    edgecolors=INK_SOFT,
    linewidth=0.4,
)

cbar = fig.colorbar(points, ax=ax, pad=0.02)
cbar.set_label(WIND_SPEED, fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_title("scatter-color-mapped · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.set_xlabel(LATITUDE, fontsize=10, color=INK)
ax.set_ylabel(LONGITUDE, fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8, color=INK)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

fig.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
