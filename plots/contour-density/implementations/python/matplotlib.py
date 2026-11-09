""" anyplot.ai
contour-density: Density Contour Plot
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 79/100 | Updated: 2026-05-16
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import PercentFormatter
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint: brand green, and the sequential Imprint colormap for the density bands
BRAND = "#009E73"
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", [BRAND, "#4467A3"])

# Constants
BAND_FLOOR = 0.10  # share of the peak density below which nothing is filled
BANDS = 9  # filled density bands between the floor and the peak
BANDWIDTH = 0.3  # KDE bandwidth factor: narrow enough to keep separate clusters apart

# Columns: set these to your table's column names
DURATION = "Eruption duration (min)"  # role: x
WAITING = "Waiting time to next eruption (min)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("eruptions.csv")
# Geyser eruptions: short eruptions follow short waits, long eruptions follow long waits
np.random.seed(42)
short_eruptions = np.random.multivariate_normal([2.0, 54.5], [[0.08, 0.5], [0.5, 34.0]], 150)
long_eruptions = np.random.multivariate_normal([4.35, 80.0], [[0.16, 0.9], [0.9, 36.0]], 300)
eruptions = np.vstack([short_eruptions, long_eruptions])
df = pd.DataFrame({DURATION: eruptions[:, 0], WAITING: eruptions[:, 1]})

# Plot: reads only df and the constants above
points = df[[DURATION, WAITING]].dropna().astype(float)
x_span = points[DURATION].max() - points[DURATION].min()
y_span = points[WAITING].max() - points[WAITING].min()
xx, yy = np.meshgrid(
    np.linspace(points[DURATION].min() - 0.08 * x_span, points[DURATION].max() + 0.08 * x_span, 240),
    np.linspace(points[WAITING].min() - 0.08 * y_span, points[WAITING].max() + 0.08 * y_span, 240),
)
kde = stats.gaussian_kde(points.to_numpy().T, bw_method=BANDWIDTH)
density = kde(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
relative = density / density.max()
levels = np.linspace(BAND_FLOOR, 1.0, BANDS + 1)
band_alpha = np.linspace(0.45, 1.0, BANDS)  # denser bands are drawn more opaque

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG, layout="constrained")
ax.set_facecolor(PAGE_BG)
bands = ax.contourf(xx, yy, relative, levels=levels, cmap=imprint_seq, zorder=1)
bands.set_alpha(band_alpha)
rings = ax.contour(xx, yy, relative, levels=levels, colors=PAGE_BG, linewidths=0.7, zorder=2)
ax.scatter(points[DURATION], points[WAITING], s=5, color=INK, alpha=0.4, linewidths=0, zorder=3)

cbar = fig.colorbar(bands, ax=ax, pad=0.02, fraction=0.035, aspect=24)
cbar.ax.set_facecolor(PAGE_BG)
cbar.solids.set_alpha(band_alpha)
cbar.add_lines(rings)
cbar.set_label("Point density (% of peak)", fontsize=9, color=INK)
cbar.ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
cbar.ax.tick_params(labelsize=8, colors=INK_SOFT, length=0)
cbar.outline.set_visible(False)

# Style
ax.set_title("contour-density · python · matplotlib · anyplot.ai", fontsize=12, fontweight="bold", color=INK)
ax.set_xlabel(DURATION, fontsize=10, color=INK)
ax.set_ylabel(WAITING, fontsize=10, color=INK)
ax.set_xlim(xx.min(), xx.max())
ax.set_ylim(yy.min(), yy.max())
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
