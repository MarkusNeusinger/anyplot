""" anyplot.ai
bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
Library: matplotlib 3.11.0 | Python 3.13.13
Quality: 88/100 | Created: 2026-06-14
"""

import os
import pathlib
import sys


# Remove this script's directory from sys.path so `import matplotlib` resolves
# to the installed package, not this file (which shares the name).
_HERE = str(pathlib.Path(__file__).parent.resolve())
sys.path = [p for p in sys.path if p != _HERE]

import matplotlib.pyplot as plt
import numpy as np


# Save outputs next to this script regardless of CWD
_OUT = pathlib.Path(__file__).parent

# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Semantic zone colors — fitness convention: grey / blue / green / ochre / red
# Imprint palette members chosen by semantic exception (each zone has a strong hue convention)
ZONE_COLORS = [INK_MUTED, "#4467A3", "#009E73", "#BD8233", "#AE3030"]

# Data — 60-minute tempo run
zone_ids = ["Z1", "Z2", "Z3", "Z4", "Z5"]
zone_names = ["Recovery", "Endurance", "Aerobic", "Threshold", "Maximum"]
minutes = [8, 22, 15, 12, 3]
hr_ranges = ["< 115 bpm", "115–138 bpm", "138–156 bpm", "156–169 bpm", "> 169 bpm"]

bar_labels = [f"{m} min" for m in minutes]
tick_labels = [f"{zid}  {name}\n{hr}" for zid, name, hr in zip(zone_ids, zone_names, hr_ranges, strict=True)]

# Plot
x = np.arange(len(zone_ids))
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

bars = ax.bar(x, minutes, color=ZONE_COLORS, width=0.55, zorder=2, edgecolor=PAGE_BG, linewidth=1.5)

for bar, label in zip(bars, bar_labels, strict=True):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.45,
        label,
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color=INK,
    )

# Style
title = "bar-heart-rate-zones · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=14)
ax.set_ylabel("Time (minutes)", fontsize=10, color=INK, labelpad=10)
ax.set_xlabel("Heart Rate Training Zone", fontsize=10, color=INK, labelpad=14)

ax.set_xticks(x)
ax.set_xticklabels(tick_labels, fontsize=8, color=INK_SOFT)
ax.tick_params(axis="both", which="both", length=0, labelsize=8, labelcolor=INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK, zorder=0)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.set_xlim(-0.6, 4.6)
ax.set_ylim(0, max(minutes) * 1.22)

fig.subplots_adjust(left=0.12, right=0.97, top=0.88, bottom=0.24)

# Save
plt.savefig(_OUT / f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
