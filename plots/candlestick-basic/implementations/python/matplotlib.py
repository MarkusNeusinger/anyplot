"""anyplot.ai
candlestick-basic: Basic Candlestick Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-30
"""

import os

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint semantic exception: finance gain/loss -> brand green (position 1) / matte red (position 5)
COLOR_UP = IMPRINT_PALETTE[0]
COLOR_DOWN = IMPRINT_PALETTE[4]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open (USD)"  # role: open
HIGH = "High (USD)"  # role: high
LOW = "Low (USD)"  # role: low
CLOSE = "Close (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
np.random.seed(42)
n_days = 30
dates = pd.bdate_range(start="2024-01-02", periods=n_days)

# Random walk prices starting at $150
returns = np.random.randn(n_days) * 0.02
price_series = 150 * np.exp(np.cumsum(returns))

# Generate OHLC from base prices
open_prices = price_series * (1 + np.random.uniform(-0.005, 0.005, n_days))
close_prices = price_series * (1 + np.random.uniform(-0.015, 0.015, n_days))
intraday_ranges = price_series * np.random.uniform(0.01, 0.03, n_days)
low_prices = np.minimum(open_prices, close_prices) - np.random.uniform(0, 0.5, n_days) * intraday_ranges
high_prices = np.maximum(open_prices, close_prices) + np.random.uniform(0, 0.5, n_days) * intraday_ranges

df = pd.DataFrame({DATE: dates, OPEN: open_prices, HIGH: high_prices, LOW: low_prices, CLOSE: close_prices})

# Plot: reads only df and the constants above
y_min_data, y_max_data = df[LOW].min(), df[HIGH].max()
min_body = (y_max_data - y_min_data) * 0.004  # scales with axis range; keeps doji bodies visible

fig = plt.figure(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax = fig.add_subplot(111)
ax.set_facecolor(PAGE_BG)

bullish = df[CLOSE] >= df[OPEN]
colors = np.where(bullish, COLOR_UP, COLOR_DOWN)
date_nums = mdates.date2num(df[DATE])
width = 0.6

# Wicks: thin lines for the high-low range, behind the bodies
ax.vlines(date_nums, df[LOW], df[HIGH], colors=colors, linewidth=1.5, zorder=1)

# Bodies: bars for the open-close range, in front of the wicks
body_bottoms = np.where(bullish, df[OPEN], df[CLOSE])
body_heights = np.maximum(np.abs(df[CLOSE] - df[OPEN]), min_body)
ax.bar(
    date_nums, body_heights, bottom=body_bottoms, width=width, color=colors, edgecolor=colors, linewidth=0.8, zorder=2
)

# Style
title = "candlestick-basic · python · matplotlib · anyplot.ai"
title_fontsize = max(8, round(12 * 67 / len(title))) if len(title) > 67 else 12

ax.set_title(title, fontsize=title_fontsize, fontweight="medium", color=INK, pad=10)
ax.set_xlabel(DATE, fontsize=10, color=INK)
ax.set_ylabel("Price (USD)", fontsize=10, color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT, labelcolor=INK_SOFT)

ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.tick_params(which="minor", length=0)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_linewidth(0.6)
    ax.spines[side].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color=INK)
ax.set_axisbelow(True)

# Legend: direction colors
legend_handles = [
    mpatches.Patch(color=COLOR_UP, label="Bullish (Close ≥ Open)"),
    mpatches.Patch(color=COLOR_DOWN, label="Bearish (Close < Open)"),
]
leg = ax.legend(
    handles=legend_handles, fontsize=8, loc="upper right", framealpha=0.9, edgecolor=INK_SOFT, facecolor=ELEVATED_BG
)
for t in leg.get_texts():
    t.set_color(INK_SOFT)

# Axis limits with padding, from the data
y_pad = (y_max_data - y_min_data) * 0.12
ax.set_ylim(y_min_data - y_pad, y_max_data + y_pad * 2.5)
ax.set_xlim(date_nums.min() - 1, date_nums.max() + 1)

fig.subplots_adjust(left=0.09, right=0.97, top=0.92, bottom=0.12)

# Save
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
