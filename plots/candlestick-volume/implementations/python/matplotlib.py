"""anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-16
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP_COLOR = IMPRINT_PALETTE[0]  # green: close at or above open
DOWN_COLOR = IMPRINT_PALETTE[4]  # red: close below open

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open ($)"  # role: open
HIGH = "High ($)"  # role: high
LOW = "Low ($)"  # role: low
CLOSE = "Close ($)"  # role: close
VOLUME = "Volume (shares)"  # role: volume

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
np.random.seed(42)
n_days = 60
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")

base_price = 150.0
returns = np.random.normal(0.001, 0.02, n_days)
prices = base_price * np.cumprod(1 + returns)

opens = np.zeros(n_days)
closes = np.zeros(n_days)
opens[0] = base_price
closes[0] = prices[0]
for i in range(1, n_days):
    opens[i] = closes[i - 1] * (1 + np.random.normal(0, 0.005))
    closes[i] = prices[i]

body_top = np.maximum(opens, closes)
body_bottom = np.minimum(opens, closes)
highs = body_top + np.zeros(n_days)
lows = body_bottom + np.zeros(n_days)
for i in range(n_days):
    highs[i] = body_top[i] + np.random.uniform(0.5, 2.0)
    lows[i] = body_bottom[i] - np.random.uniform(0.5, 2.0)

# Volume rises with the size of the day's move
volume_multiplier = 1 + np.abs(closes - opens) / opens * 20
volumes = (5_000_000 * volume_multiplier * np.random.uniform(0.7, 1.3, n_days)).astype(int)

df = pd.DataFrame({DATE: dates, OPEN: opens, HIGH: highs, LOW: lows, CLOSE: closes, VOLUME: volumes})

# Plot: reads only df and the constants above
is_up = (df[CLOSE] >= df[OPEN]).to_numpy()
colors = np.where(is_up, UP_COLOR, DOWN_COLOR)
x = mdates.date2num(df[DATE])
body_low = df[[OPEN, CLOSE]].min(axis=1)
body_height = (df[CLOSE] - df[OPEN]).abs()
candle_width = 0.6

fig, (ax_price, ax_volume) = plt.subplots(
    2, 1, figsize=(8, 4.5), dpi=400, gridspec_kw={"height_ratios": [3, 1]}, sharex=True, facecolor=PAGE_BG
)
for ax in (ax_price, ax_volume):
    ax.set_facecolor(PAGE_BG)

# Price pane: wick from low to high, body from open to close
ax_price.vlines(x, df[LOW], df[HIGH], colors=colors, linewidth=1.4, capstyle="round")
ax_price.bar(x, body_height, width=candle_width, bottom=body_low, color=colors, edgecolor=colors, linewidth=0.3)

# Volume pane: same up/down colors as the candles
ax_volume.bar(x, df[VOLUME], width=candle_width, color=colors, alpha=0.8)

# Crosshair: one vertical guide through both panes at the middle date
guide_x = x[len(x) // 2]
for ax in (ax_price, ax_volume):
    ax.axvline(guide_x, color=INK_SOFT, linestyle="--", linewidth=0.6, alpha=0.4)

# Style
title = "candlestick-volume · python · matplotlib · anyplot.ai"
ax_price.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=8)
ax_price.set_ylabel("Price ($)", fontsize=10, color=INK)
ax_volume.set_xlabel(DATE, fontsize=10, color=INK)
ax_volume.set_ylabel(VOLUME, fontsize=10, color=INK)
ax_volume.set_ylim(bottom=0)
ax_volume.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v / 1e6:.1f}M"))
ax_volume.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=12))
ax_volume.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
plt.setp(ax_volume.xaxis.get_majorticklabels(), rotation=45, ha="right")

for ax in (ax_price, ax_volume):
    ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)
    ax.grid(True, alpha=0.15, linewidth=0.5, color=INK)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_SOFT)
        ax.spines[side].set_linewidth(0.5)

legend_elements = [
    Patch(facecolor=UP_COLOR, label="Up (Close ≥ Open)"),
    Patch(facecolor=DOWN_COLOR, label="Down (Close < Open)"),
]
leg = ax_price.legend(handles=legend_elements, loc="lower left", fontsize=8)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
leg.get_frame().set_linewidth(0.5)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.09, right=0.98, top=0.93, bottom=0.17, hspace=0.08)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
