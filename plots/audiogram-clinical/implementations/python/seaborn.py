"""anyplot.ai
audiogram-clinical: Clinical Audiogram
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 87/100 | Created: 2026-06-14
"""

import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from matplotlib.transforms import blended_transform_factory


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Semantic color exception: clinical convention (right ear = red, left ear = blue)
RIGHT_COLOR = "#AE3030"  # Imprint matte red
LEFT_COLOR = "#4467A3"  # Imprint blue

# Pure-tone audiometry — high-frequency sensorineural notch (noise-induced pattern)
frequencies = [125, 250, 500, 1000, 2000, 4000, 8000]
threshold_right = [10, 10, 15, 15, 20, 55, 65]  # dB HL, right ear
threshold_left = [10, 15, 15, 20, 30, 65, 75]  # dB HL, left ear

# Severity bands [dB HL lo, hi, fill color, label]
BANDS = [
    (-10, 25, "#009E73", "Normal"),
    (25, 40, "#99B314", "Mild"),
    (40, 55, "#BD8233", "Moderate"),
    (55, 70, "#DDCC77", "Mod. Severe"),
    (70, 90, "#AE3030", "Severe"),
    (90, 120, "#954477", "Profound"),
]
BAND_ALPHA = 0.09 if THEME == "light" else 0.16

# Global seaborn theme
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

# Canvas — square (2400×2400 px); audiogram is a square clinical grid
fig, ax = plt.subplots(figsize=(6, 6), dpi=400)
fig.set_facecolor(PAGE_BG)
ax.set_facecolor(PAGE_BG)
fig.subplots_adjust(left=0.11, right=0.80, top=0.92, bottom=0.12)

# Severity band fills (drawn first, behind everything)
for y_lo, y_hi, color, _ in BANDS:
    ax.axhspan(y_lo, y_hi, alpha=BAND_ALPHA, color=color, zorder=0)

# Log x-scale and inverted y-axis
ax.set_xscale("log")
ax.set_xlim(100, 9000)
ax.set_ylim(120, -10)

# Right ear: red open circles, solid line
sns.lineplot(
    x=frequencies,
    y=threshold_right,
    color=RIGHT_COLOR,
    linewidth=2.0,
    linestyle="-",
    marker="o",
    markersize=9,
    markerfacecolor=PAGE_BG,
    markeredgecolor=RIGHT_COLOR,
    markeredgewidth=2.0,
    label="Right Ear (O)",
    zorder=4,
    ax=ax,
)

# Left ear: blue crosses, dashed line
sns.lineplot(
    x=frequencies,
    y=threshold_left,
    color=LEFT_COLOR,
    linewidth=2.0,
    linestyle="--",
    marker="x",
    markersize=10,
    markeredgewidth=2.5,
    label="Left Ear (X)",
    zorder=4,
    ax=ax,
)

# x-axis: audiometric frequencies only, log scale
ax.set_xticks(frequencies)
ax.xaxis.set_major_formatter(ticker.FixedFormatter(["125", "250", "500", "1k", "2k", "4k", "8k"]))
ax.xaxis.set_minor_locator(ticker.NullLocator())

# y-axis: 10 dB steps from -10 to 120
ax.set_yticks(range(-10, 121, 10))

# Grid on both axes (standard clinical audiogram appearance)
ax.set_axisbelow(True)
ax.xaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)

# Severity band labels in right margin
trans = blended_transform_factory(ax.transAxes, ax.transData)
for y_lo, y_hi, _, label in BANDS:
    ax.text(
        1.04,
        (y_lo + y_hi) / 2,
        label,
        transform=trans,
        va="center",
        ha="left",
        fontsize=7,
        color=INK_MUTED,
        style="italic",
        clip_on=False,
    )

# Axis labels and tick styling
ax.set_xlabel("Frequency (Hz)", fontsize=10, color=INK, labelpad=8)
ax.set_ylabel("Hearing Level (dB HL)", fontsize=10, color=INK, labelpad=8)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, top=False, right=False)

# Title
title = "audiogram-clinical · python · seaborn · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=10)

# Legend
legend = ax.legend(fontsize=8, loc="lower left", facecolor=ELEVATED_BG, edgecolor=INK_SOFT, framealpha=0.9)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

# Spines — seaborn idiom removes top/right; color remaining spines
sns.despine(ax=ax)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
