"""anyplot.ai
climograph-walter-lieth: Walter-Lieth Climate Diagram
Library: seaborn | Python 3.13
Quality: pending | Created: 2026-06-15
"""

import os
import sys


# Prevent the script directory from shadowing the seaborn package on sys.path
_this_dir = os.path.abspath(os.path.dirname(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _this_dir]

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — semantic assignments
# Temperature → matte red (Imprint slot 5, semantic: heat)
# Precipitation → blue (Imprint slot 3, semantic: water/sky)
TEMP_COLOR = "#AE3030"
PRECIP_COLOR = "#4467A3"

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

# Station: Mediterranean climate — warm dry summers, mild wet winters
STATION = "Porto Vell"
ELEVATION = 88
PERIOD = "1991–2020"

MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
TEMPERATURE = np.array([10.5, 11.5, 13.5, 16.5, 20.5, 25.0, 28.5, 29.0, 25.5, 20.5, 15.0, 11.5])
PRECIP = np.array([58, 42, 38, 30, 22, 8, 4, 8, 36, 62, 72, 65])

T_MEAN = round(TEMPERATURE.mean(), 1)
P_TOTAL = int(PRECIP.sum())

# Walter-Lieth scaling: 10°C = 20 mm → divide precipitation by 2 to plot on temp axis
precip_t = PRECIP / 2.0
x = np.arange(12)

Y_MIN = -6
Y_MAX = max(TEMPERATURE.max(), precip_t.max()) + 5  # ~41

# Figure (landscape 3200×1800)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Fill between curves: humid (blue) where precip > temp, arid (red) where temp > precip
ax.fill_between(
    x, TEMPERATURE, precip_t, where=precip_t >= TEMPERATURE, color=PRECIP_COLOR, alpha=0.25, interpolate=True
)
ax.fill_between(x, TEMPERATURE, precip_t, where=TEMPERATURE >= precip_t, color=TEMP_COLOR, alpha=0.20, interpolate=True)

# Temperature and precipitation lines
sns.lineplot(x=x, y=TEMPERATURE, ax=ax, color=TEMP_COLOR, linewidth=2.5, zorder=3)
sns.lineplot(x=x, y=precip_t, ax=ax, color=PRECIP_COLOR, linewidth=2.5, zorder=3)

# Right precipitation axis (scaled 2:1 against temperature)
ax2 = ax.twinx()
ax2.set_ylim(Y_MIN * 2, Y_MAX * 2)
ax2.set_yticks([0, 20, 40, 60, 80])
ax2.tick_params(axis="y", labelsize=8, colors=PRECIP_COLOR)
ax2.set_ylabel("Precipitation (mm)", fontsize=10, color=PRECIP_COLOR, labelpad=8)
ax2.spines["right"].set_color(PRECIP_COLOR)
ax2.spines["top"].set_visible(False)
ax2.spines["bottom"].set_visible(False)
ax2.spines["left"].set_visible(False)

# Zero-degree reference line
ax.axhline(0, color=INK_SOFT, linewidth=0.8, linestyle="--", alpha=0.5, zorder=1)

# Frost month indicators: solid blue band below 0°C for months with mean T < 0°C
for i, t in enumerate(TEMPERATURE):
    if t < 0:
        ax.fill_between([i - 0.45, i + 0.45], [Y_MIN, Y_MIN], [0, 0], color=PRECIP_COLOR, alpha=0.45, zorder=2)

# Left (temperature) axis styling
ax.set_ylim(Y_MIN, Y_MAX)
ax.set_xlim(-0.5, 11.5)
ax.set_xticks(x)
ax.set_xticklabels(MONTHS, fontsize=8)
ax.set_yticks([0, 10, 20, 30, 40])
ax.tick_params(axis="y", colors=TEMP_COLOR, labelsize=8)
ax.set_ylabel("Temperature (°C)", fontsize=10, color=TEMP_COLOR, labelpad=6)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(TEMP_COLOR)
ax.spines["bottom"].set_color(INK_SOFT)
ax.yaxis.grid(True, alpha=0.12, linewidth=0.8, color=INK, zorder=0)

# Legend with proxy artists
leg = ax.legend(
    handles=[
        mlines.Line2D([], [], color=TEMP_COLOR, linewidth=2.5, label="Temperature"),
        mlines.Line2D([], [], color=PRECIP_COLOR, linewidth=2.5, label="Precipitation"),
        mpatches.Patch(facecolor=PRECIP_COLOR, alpha=0.4, label="Humid period"),
        mpatches.Patch(facecolor=TEMP_COLOR, alpha=0.35, label="Arid period"),
    ],
    fontsize=7.5,
    loc="upper left",
    facecolor=ELEVATED_BG,
    edgecolor=INK_SOFT,
    framealpha=0.9,
)
for text in leg.get_texts():
    text.set_color(INK)

# Station header
header = f"{STATION}  ·  {ELEVATION} m  ·  {PERIOD}    T = {T_MEAN} °C  ·  P = {P_TOTAL} mm"
ax.text(
    0.5,
    0.97,
    header,
    transform=ax.transAxes,
    ha="center",
    va="top",
    fontsize=8.5,
    color=INK,
    bbox={"boxstyle": "round,pad=0.35", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
)

# Title
title = "climograph-walter-lieth · python · seaborn · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_fontsize = max(8, round(12 * ratio))
ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)

# Layout and save
fig.subplots_adjust(left=0.09, right=0.88, bottom=0.09, top=0.84)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
