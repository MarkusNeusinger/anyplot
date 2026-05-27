"""
line-navigator: Line Chart with Mini Navigator
Library: matplotlib | Python
"""

import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

BRAND = "#009E73"
ANYPLOT_AMBER = "#DDCC77"

# Data — daily temperature sensor readings over 3 years (1095 data points)
np.random.seed(42)
dates = pd.date_range("2022-01-01", periods=1095, freq="D")

trend = np.linspace(20, 25, 1095)
seasonal = 8 * np.sin(2 * np.pi * np.arange(1095) / 365)
noise = np.random.randn(1095) * 1.5
values = trend + seasonal + noise

# Selected range shown in main chart (~4 months)
selected_start = 400
selected_end = 520

fig, (ax_main, ax_nav) = plt.subplots(2, 1, figsize=(8, 4.5), dpi=400, height_ratios=[4, 1], sharex=False)
fig.patch.set_facecolor(PAGE_BG)
fig.subplots_adjust(left=0.08, right=0.97, top=0.91, bottom=0.12, hspace=0.38)

# --- Main chart ---
ax_main.set_facecolor(PAGE_BG)
ax_main.plot(dates[selected_start:selected_end], values[selected_start:selected_end], linewidth=2.5, color=BRAND)
ax_main.fill_between(dates[selected_start:selected_end], values[selected_start:selected_end], alpha=0.15, color=BRAND)

title = "line-navigator · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12
ax_main.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=6)
ax_main.set_ylabel("Temperature (°C)", fontsize=10, color=INK)
ax_main.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
ax_main.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax_main.spines["top"].set_visible(False)
ax_main.spines["right"].set_visible(False)
ax_main.spines["left"].set_color(INK_SOFT)
ax_main.spines["bottom"].set_color(INK_SOFT)

ax_main.set_xlim(dates[selected_start], dates[selected_end])
y_min = values[selected_start:selected_end].min()
y_max = values[selected_start:selected_end].max()
y_pad = (y_max - y_min) * 0.12
ax_main.set_ylim(y_min - y_pad, y_max + y_pad)

date_range_text = f"{dates[selected_start].strftime('%b %d, %Y')} — {dates[selected_end - 1].strftime('%b %d, %Y')}"
ax_main.annotate(
    date_range_text,
    xy=(0.99, 0.97),
    xycoords="axes fraction",
    fontsize=8,
    ha="right",
    va="top",
    color=INK_SOFT,
    bbox={"boxstyle": "round,pad=0.3", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.9},
)

# --- Navigator chart ---
ax_nav.set_facecolor(PAGE_BG)
ax_nav.plot(dates, values, linewidth=1.0, color=BRAND, alpha=0.7)
ax_nav.fill_between(dates, values, alpha=0.1, color=BRAND)

ax_nav.set_xlabel("Date", fontsize=10, color=INK)
ax_nav.tick_params(axis="both", labelsize=7, colors=INK_SOFT, labelcolor=INK_SOFT)
ax_nav.spines["top"].set_visible(False)
ax_nav.spines["right"].set_visible(False)
ax_nav.spines["left"].set_visible(False)
ax_nav.spines["bottom"].set_color(INK_SOFT)
ax_nav.set_yticks([])

ax_nav.set_xlim(dates[0], dates[-1])
v_range = values.max() - values.min()
y_nav_min = values.min() - v_range * 0.08
y_nav_max = values.max() + v_range * 0.08
ax_nav.set_ylim(y_nav_min, y_nav_max)

# Gray out non-selected regions
ax_nav.axvspan(dates[0], dates[selected_start], alpha=0.3, color=INK_MUTED)
ax_nav.axvspan(dates[selected_end], dates[-1], alpha=0.3, color=INK_MUTED)

# Selection window rectangle
selection_rect = mpatches.Rectangle(
    (dates[selected_start], y_nav_min),
    dates[selected_end] - dates[selected_start],
    y_nav_max - y_nav_min,
    linewidth=1.5,
    edgecolor=ANYPLOT_AMBER,
    facecolor=ANYPLOT_AMBER,
    alpha=0.25,
    zorder=5,
)
ax_nav.add_patch(selection_rect)

# Selection edge handles
ax_nav.axvline(dates[selected_start], color=ANYPLOT_AMBER, linewidth=2.0, zorder=6)
ax_nav.axvline(dates[selected_end], color=ANYPLOT_AMBER, linewidth=2.0, zorder=6)

# Navigator label
ax_nav.annotate(
    "Navigator",
    xy=(0.01, 0.90),
    xycoords="axes fraction",
    fontsize=7,
    ha="left",
    va="top",
    fontweight="bold",
    color=INK_MUTED,
)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
plt.close()
