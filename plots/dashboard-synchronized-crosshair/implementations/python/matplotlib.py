"""anyplot.ai
dashboard-synchronized-crosshair: Synchronized Multi-Chart Dashboard
Library: matplotlib | Python 3.13
Quality: pending | Created: 2026-05-23
"""

import os
import sys


# Prevent this file from shadowing the installed matplotlib package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p and os.path.abspath(p) != _here]

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.dates import DateFormatter, MonthLocator


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # anyplot palette position 1 — always first series
COLOR_2 = "#9418DB"  # position 2 — RSI line
COLOR_RED = "#B71D27"  # position 3 — semantic: down / overbought

# Data — stock-like time series: price, volume, RSI
np.random.seed(42)
n_points = 200
dates = pd.date_range("2024-01-01", periods=n_points, freq="B")

price = 100 + np.cumsum(np.random.randn(n_points) * 2 + 0.05)
volume = np.abs(np.diff(price, prepend=price[0])) * 1e6 + np.random.uniform(0.5e6, 2e6, n_points)
rsi_raw = 50 + np.cumsum(np.random.randn(n_points) * 3)
rsi_raw = np.clip(rsi_raw, 10, 90)
rsi = 30 + (rsi_raw - rsi_raw.min()) / (rsi_raw.max() - rsi_raw.min()) * 40

# Canvas — square 2400×2400 for 3-panel vertical stack
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(6, 6), dpi=400, facecolor=PAGE_BG, sharex=True)
fig.subplots_adjust(left=0.13, right=0.97, top=0.93, bottom=0.12, hspace=0.08)

for ax in (ax1, ax2, ax3):
    ax.set_facecolor(PAGE_BG)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(INK_SOFT)
    ax.tick_params(axis="y", labelsize=7, colors=INK_SOFT)
    ax.yaxis.grid(True, alpha=0.12, linewidth=0.6, color=INK)
    ax.set_axisbelow(True)

# Chart 1: Price
ax1.plot(dates, price, color=BRAND, linewidth=2.0, label="Price")
ax1.fill_between(dates, price, alpha=0.10, color=BRAND)
price_pad = (price.max() - price.min()) * 0.12
ax1.set_ylim(price.min() - price_pad, price.max() + price_pad)
ax1.set_ylabel("Price ($)", fontsize=8, color=INK)
leg1 = ax1.legend(fontsize=7, loc="upper left")
leg1.get_frame().set_facecolor(ELEVATED_BG)
leg1.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg1.get_texts(), color=INK_SOFT)
ax1.spines["bottom"].set_visible(False)
ax1.set_title(
    "dashboard-synchronized-crosshair · python · matplotlib · anyplot.ai",
    fontsize=10,
    fontweight="medium",
    color=INK,
    pad=6,
)

# Chart 2: Volume — semantic coloring (green=up, red=down)
vol_colors = [BRAND if price[i] >= price[max(0, i - 1)] else COLOR_RED for i in range(n_points)]
ax2.bar(dates, volume / 1e6, color=vol_colors, alpha=0.75, width=1.3, label="Volume")
ax2.set_ylabel("Volume (M)", fontsize=8, color=INK)
leg2 = ax2.legend(fontsize=7, loc="upper left")
leg2.get_frame().set_facecolor(ELEVATED_BG)
leg2.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg2.get_texts(), color=INK_SOFT)
ax2.spines["bottom"].set_visible(False)

# Chart 3: RSI
ax3.plot(dates, rsi, color=COLOR_2, linewidth=2.0, label="RSI")
ax3.axhline(y=70, color=COLOR_RED, linestyle="--", linewidth=1.0, alpha=0.7)
ax3.axhline(y=30, color=BRAND, linestyle="--", linewidth=1.0, alpha=0.7)
ax3.fill_between(dates, 30, 70, alpha=0.06, color=INK_SOFT)
ax3.text(dates[-1], 70.5, "Overbought", fontsize=6, color=COLOR_RED, ha="right", va="bottom")
ax3.text(dates[-1], 29.5, "Oversold", fontsize=6, color=BRAND, ha="right", va="top")
ax3.set_ylabel("RSI", fontsize=8, color=INK)
ax3.set_xlabel("Date", fontsize=8, color=INK)
ax3.set_ylim(18, 82)
ax3.spines["bottom"].set_color(INK_SOFT)
ax3.tick_params(axis="x", labelsize=7, colors=INK_SOFT)
ax3.xaxis.set_major_formatter(DateFormatter("%b '%y"))
ax3.xaxis.set_major_locator(MonthLocator(bymonth=[1, 4, 7, 10]))
leg3 = ax3.legend(fontsize=7, loc="upper left")
leg3.get_frame().set_facecolor(ELEVATED_BG)
leg3.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg3.get_texts(), color=INK_SOFT)

# Synchronized crosshair demonstration — static snapshot at a meaningful date
crosshair_idx = 120
crosshair_date = dates[crosshair_idx]
crosshair_price = price[crosshair_idx]
crosshair_vol = volume[crosshair_idx] / 1e6
crosshair_rsi = rsi[crosshair_idx]

for ax in (ax1, ax2, ax3):
    ax.axvline(x=crosshair_date, color=INK_MUTED, linestyle="-", linewidth=1.0, alpha=0.6)

ann_kw = {
    "xytext": (6, 4),
    "textcoords": "offset points",
    "fontsize": 7,
    "fontweight": "bold",
    "color": INK,
    "bbox": {"boxstyle": "round,pad=0.2", "facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "alpha": 0.92},
}
ax1.annotate(f"${crosshair_price:.1f}", xy=(crosshair_date, crosshair_price), **ann_kw)
ax1.scatter([crosshair_date], [crosshair_price], color=BRAND, s=40, zorder=5, edgecolors=PAGE_BG, linewidths=0.5)

ax2.annotate(f"{crosshair_vol:.1f}M", xy=(crosshair_date, crosshair_vol), **ann_kw)

ax3.annotate(f"RSI {crosshair_rsi:.1f}", xy=(crosshair_date, crosshair_rsi), **ann_kw)
ax3.scatter([crosshair_date], [crosshair_rsi], color=COLOR_2, s=40, zorder=5, edgecolors=PAGE_BG, linewidths=0.5)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
