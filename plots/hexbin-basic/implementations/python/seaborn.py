"""anyplot.ai
hexbin-basic: Basic Hexbin Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: pending | Updated: 2026-05-29
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap, LogNorm


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential ramp for colored cells filling the plot (fields stops)
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", SEQ_FIELDS)

# Constants
GRIDSIZE = 35

# Columns
LONGITUDE = "Longitude (°E)"  # role: x
LATITUDE = "Latitude (°N)"  # role: y

# Data — NYC GPS coordinates for urban traffic hotspot analysis
np.random.seed(42)
n_points = 50000

downtown = np.random.multivariate_normal([-73.985, 40.748], [[0.0001, 0.00005], [0.00005, 0.0001]], n_points // 2)
airport = np.random.multivariate_normal([-73.875, 40.775], [[0.00008, -0.00003], [-0.00003, 0.00008]], n_points // 3)
shopping = np.random.multivariate_normal([-73.965, 40.785], [[0.00004, 0], [0, 0.00006]], n_points // 6)

df = pd.DataFrame(
    {
        LONGITUDE: np.concatenate([downtown[:, 0], airport[:, 0], shopping[:, 0]]),
        LATITUDE: np.concatenate([downtown[:, 1], airport[:, 1], shopping[:, 1]]),
    }
)

# Plot
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.15,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Landscape canvas: 8 x 4.5 in @ dpi=400 -> 3200x1800 px
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)

# Hexbin with log-normalized counts so sparse fringes and dense cores both read
hb = ax.hexbin(
    df[LONGITUDE], df[LATITUDE], gridsize=GRIDSIZE, cmap=imprint_seq, mincnt=1, norm=LogNorm(), edgecolors="none"
)

ax.set_xlabel(LONGITUDE, fontsize=10)
ax.set_ylabel(LATITUDE, fontsize=10)
ax.set_title("hexbin-basic · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8)
ax.grid(True, linewidth=0.8)
ax.set_axisbelow(True)
sns.despine(ax=ax)

# Colorbar
cbar = fig.colorbar(hb, ax=ax, pad=0.02)
cbar.set_label("Point count (log scale)", fontsize=10, color=INK)
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT)
cbar.outline.set_edgecolor(INK_SOFT)

# Save
plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
