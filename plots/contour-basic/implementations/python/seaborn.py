"""anyplot.ai
contour-basic: Basic Contour Plot
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 87/100 | Updated: 2026-06-25
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential colormap for continuous density data
imprint_seq = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Data — bivariate distribution of weather-station readings across two synoptic regimes
np.random.seed(42)
cold_front = np.random.multivariate_normal(mean=[4.8, 1021.5], cov=[[3.2, -1.3], [-1.3, 7.8]], size=1500)
warm_front = np.random.multivariate_normal(mean=[11.6, 1013.2], cov=[[6.0, 2.0], [2.0, 5.0]], size=900)
readings = pd.DataFrame(np.vstack([cold_front, warm_front]), columns=["Wind Speed (m/s)", "Barometric Pressure (hPa)"])

# Theme
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
        "axes.linewidth": 0.9,
        "axes.axisbelow": True,
    },
)

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400)
fig.set_facecolor(PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Filled KDE contours — seaborn's kdeplot with integrated colorbar (Imprint sequential cmap)
sns.kdeplot(
    data=readings,
    x="Wind Speed (m/s)",
    y="Barometric Pressure (hPa)",
    fill=True,
    cmap=imprint_seq,
    thresh=0.02,
    levels=12,
    cbar=True,
    cbar_kws={"shrink": 0.85, "pad": 0.02, "label": "Reading Density"},
    ax=ax,
)

# Isoline overlay via scipy KDE grid — returns ContourSet needed for ax.clabel
x_vals = readings["Wind Speed (m/s)"].values
y_vals = readings["Barometric Pressure (hPa)"].values
kde = gaussian_kde(np.vstack([x_vals, y_vals]))
x_grid = np.linspace(x_vals.min() - 1, x_vals.max() + 1, 80)
y_grid = np.linspace(y_vals.min() - 2, y_vals.max() + 2, 80)
XX, YY = np.meshgrid(x_grid, y_grid)
ZZ = kde(np.vstack([XX.ravel(), YY.ravel()])).reshape(XX.shape)
cs = ax.contour(XX, YY, ZZ, levels=10, colors=INK, alpha=0.35, linewidths=0.7)
ax.clabel(cs, levels=cs.levels[2::3], inline=True, fontsize=15, fmt="%.3f", colors=INK)

# Style
title = "contour-basic · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=14)
ax.set_xlabel("Wind Speed (m/s)", fontsize=10, color=INK, labelpad=10)
ax.set_ylabel("Barometric Pressure (hPa)", fontsize=10, color=INK, labelpad=10)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, length=0)
sns.despine(ax=ax)

# Colorbar chrome (theme-adaptive)
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=8, colors=INK_SOFT, length=0)
cbar_ax.yaxis.label.set_color(INK)
cbar_ax.yaxis.label.set_fontsize(9)
cbar_ax.set_facecolor(ELEVATED_BG)
for spine in cbar_ax.spines.values():
    spine.set_color(INK_SOFT)
    spine.set_linewidth(0.8)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
