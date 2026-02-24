""" pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 83/100 | Updated: 2026-02-24
"""

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd


# Data - Generate realistic stock price data for 30 trading days
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

df = pd.DataFrame({"date": dates, "open": open_prices, "high": high_prices, "low": low_prices, "close": close_prices})

# Plot
fig, ax = plt.subplots(figsize=(16, 9))

bullish = df["close"] >= df["open"]
color_up = "#26a69a"
color_down = "#ef5350"
colors = np.where(bullish, color_up, color_down)
date_nums = mdates.date2num(df["date"])
width = 0.6

# Wicks — thin lines for high-low range (behind bodies)
ax.vlines(date_nums, df["low"], df["high"], colors=colors, linewidth=1.2, zorder=1)

# Bodies — bars for open-close range (in front of wicks)
body_bottoms = np.where(bullish, df["open"], df["close"])
body_heights = np.abs(df["close"] - df["open"])
body_heights = np.where(body_heights < 0.01, 0.01, body_heights)
ax.bar(
    date_nums, body_heights, bottom=body_bottoms, width=width, color=colors, edgecolor=colors, linewidth=0.8, zorder=2
)

# Date formatting
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_minor_locator(mdates.DayLocator())

# Style
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price", fontsize=20)
ax.set_title("candlestick-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium")
ax.tick_params(axis="both", labelsize=16)
ax.tick_params(axis="x", rotation=45)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Y-axis dollar formatting
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))

# Subtle y-axis grid for reading price levels
ax.yaxis.grid(True, alpha=0.2, linewidth=0.8)
ax.set_axisbelow(True)

# Legend
legend_handles = [
    mpatches.Patch(color=color_up, label="Bullish (Close \u2265 Open)"),
    mpatches.Patch(color=color_down, label="Bearish (Close < Open)"),
]
ax.legend(handles=legend_handles, fontsize=16, loc="upper right", framealpha=0.9, edgecolor="none")

# Axis limits with padding
y_min, y_max = df["low"].min(), df["high"].max()
y_pad = (y_max - y_min) * 0.1
ax.set_ylim(y_min - y_pad, y_max + y_pad)
x_min = mdates.date2num(df["date"].min())
x_max = mdates.date2num(df["date"].max())
ax.set_xlim(x_min - 1, x_max + 1)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
