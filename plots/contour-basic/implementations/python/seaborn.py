""" anyplot.ai
contour-basic: Basic Contour Plot
Library: seaborn 0.13.2 | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-24
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — bivariate distribution of weather-station readings across two synoptic regimes
np.random.seed(42)
cold_front = np.random.multivariate_normal(mean=[4.8, 1021.5], cov=[[3.2, -1.3], [-1.3, 7.8]], size=1500)
warm_front = np.random.multivariate_normal(mean=[11.6, 1013.2], cov=[[6.0, 2.0], [2.0, 5.0]], size=900)
readings = pd.DataFrame(np.vstack([cold_front, warm_front]), columns=["Wind Speed (m/s)", "Barometric Pressure (hPa)"])

# Theme
sns.set_theme(
    context="talk",
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

fig, ax = plt.subplots(figsize=(16, 9))

# Filled KDE contours — native seaborn with integrated colorbar
sns.kdeplot(
    data=readings,
    x="Wind Speed (m/s)",
    y="Barometric Pressure (hPa)",
    fill=True,
    cmap="viridis",
    thresh=0.02,
    levels=12,
    cbar=True,
    cbar_kws={"shrink": 0.85, "pad": 0.02, "label": "Reading Density"},
    ax=ax,
)

# Overlay thin isoline contours for ridge definition
sns.kdeplot(
    data=readings,
    x="Wind Speed (m/s)",
    y="Barometric Pressure (hPa)",
    color=PAGE_BG,
    alpha=0.55,
    linewidths=0.9,
    thresh=0.02,
    levels=12,
    ax=ax,
)

# Label key contour levels (every third line) using the isoline ContourSet.
# Labels sit on viridis fill (not page background) so use a constant light ink.
isolines = ax.collections[-1]
label_levels = isolines.levels[2::3]
ax.clabel(isolines, levels=label_levels, inline=True, fontsize=13, fmt="%.3f", colors="#F0EFE8")

# Style
ax.set_title(
    "Weather Regime Density · contour-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK, pad=20
)
ax.set_xlabel("Wind Speed (m/s)", fontsize=20, color=INK, labelpad=12)
ax.set_ylabel("Barometric Pressure (hPa)", fontsize=20, color=INK, labelpad=12)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT, length=0)
sns.despine(ax=ax)

# Colorbar chrome (theme-adaptive)
cbar_ax = fig.axes[-1]
cbar_ax.tick_params(labelsize=15, colors=INK_SOFT, length=0)
cbar_ax.yaxis.label.set_color(INK)
cbar_ax.yaxis.label.set_fontsize(18)
cbar_ax.set_facecolor(ELEVATED_BG)
for spine in cbar_ax.spines.values():
    spine.set_color(INK_SOFT)
    spine.set_linewidth(0.8)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
