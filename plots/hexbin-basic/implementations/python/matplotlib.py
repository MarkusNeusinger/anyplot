"""anyplot.ai
hexbin-basic: Basic Hexbin Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Created: 2026-05-29
"""

import os

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import LogFormatterSciNotation


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp (fields stops: colored cells fill the plot), per theme
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", SEQ_FIELDS)

# Columns: set these to your table's column names
LONGITUDE = "Longitude (km)"  # role: x
LATITUDE = "Latitude (km)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("readings.csv")
# Simulated urban sensor readings with three density clusters
np.random.seed(42)
n_points = 10000
downtown_x = np.random.randn(n_points // 2) * 1.5 + 2
downtown_y = np.random.randn(n_points // 2) * 1.5 + 2
industrial_x = np.random.randn(n_points // 3) * 1.0 - 2
industrial_y = np.random.randn(n_points // 3) * 1.0 - 1
suburb_x = np.random.randn(n_points // 6) * 0.8 + 1
suburb_y = np.random.randn(n_points // 6) * 0.8 - 2
df = pd.DataFrame(
    {
        LONGITUDE: np.concatenate([downtown_x, industrial_x, suburb_x]),
        LATITUDE: np.concatenate([downtown_y, industrial_y, suburb_y]),
    }
)

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

hb = ax.hexbin(
    df[LONGITUDE],
    df[LATITUDE],
    gridsize=30,
    cmap=imprint_seq,
    mincnt=1,
    linewidths=0.2,
    edgecolors=PAGE_BG,
    norm=mcolors.LogNorm(),
)

# Colorbar with scientific-notation ticks on the log scale
cbar = fig.colorbar(hb, ax=ax, shrink=0.85, pad=0.03)
cbar.set_label("Sensor readings per hexagon (log count)", fontsize=10, color=INK)
cbar.ax.yaxis.set_major_formatter(LogFormatterSciNotation())
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
cbar.outline.set_linewidth(0.5)
cbar.outline.set_edgecolor(INK_SOFT)

# Style
ax.set_xlabel(LONGITUDE, fontsize=10, color=INK)
ax.set_ylabel(LATITUDE, fontsize=10, color=INK)

title = "hexbin-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK)

ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["left"].set_linewidth(0.5)
ax.spines["bottom"].set_color(INK_SOFT)
ax.spines["bottom"].set_linewidth(0.5)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
