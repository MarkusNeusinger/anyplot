""" pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-24
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

# Compute 5-day simple moving average for trend context
df["sma5"] = df["close"].rolling(window=5).mean()

# Plot
fig, ax = plt.subplots(figsize=(16, 9))
fig.patch.set_facecolor("#fafafa")
ax.set_facecolor("#fafafa")

bullish = df["close"] >= df["open"]

# Colorblind-safe palette: blue for bullish, orange for bearish
color_up = "#1976d2"
color_down = "#e65100"
colors = np.where(bullish, color_up, color_down)
date_nums = mdates.date2num(df["date"])
width = 0.6

# Wicks — thin lines for high-low range (behind bodies)
ax.vlines(date_nums, df["low"], df["high"], colors=colors, linewidth=1.5, zorder=1)

# Bodies — bars for open-close range (in front of wicks)
body_bottoms = np.where(bullish, df["open"], df["close"])
body_heights = np.abs(df["close"] - df["open"])
body_heights = np.where(body_heights < 0.01, 0.01, body_heights)
ax.bar(
    date_nums, body_heights, bottom=body_bottoms, width=width, color=colors, edgecolor=colors, linewidth=0.8, zorder=2
)

# 5-day moving average line for trend storytelling
sma_mask = df["sma5"].notna()
ax.plot(
    date_nums[sma_mask],
    df["sma5"][sma_mask],
    color="#37474f",
    linewidth=2.0,
    linestyle="-",
    alpha=0.7,
    zorder=3,
    label="5-day SMA",
)

# Highlight the largest single-day price drop for narrative emphasis
daily_change = df["close"] - df["open"]
biggest_drop_idx = daily_change.idxmin()
ax.annotate(
    f"Largest drop\n${daily_change[biggest_drop_idx]:.2f}",
    xy=(date_nums[biggest_drop_idx], df["low"].iloc[biggest_drop_idx]),
    xytext=(0, -32),
    textcoords="offset points",
    fontsize=13,
    fontweight="medium",
    color=color_down,
    ha="center",
    va="top",
    arrowprops={"arrowstyle": "-", "color": color_down, "lw": 1.2},
    zorder=4,
)

# Date formatting
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_minor_locator(mdates.DayLocator())

# Style
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price (USD)", fontsize=20)
ax.set_title("candlestick-basic \u00b7 matplotlib \u00b7 pyplots.ai", fontsize=24, fontweight="medium", pad=16)
ax.tick_params(axis="both", labelsize=16)
ax.tick_params(axis="x", rotation=45)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(0.6)
ax.spines["left"].set_color("#999999")
ax.spines["bottom"].set_linewidth(0.6)
ax.spines["bottom"].set_color("#999999")

# Y-axis dollar formatting
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))

# Subtle y-axis grid for reading price levels
ax.yaxis.grid(True, alpha=0.15, linewidth=0.6, color="#888888")
ax.set_axisbelow(True)

# Legend
legend_handles = [
    mpatches.Patch(color=color_up, label="Bullish (Close \u2265 Open)"),
    mpatches.Patch(color=color_down, label="Bearish (Close < Open)"),
    plt.Line2D([0], [0], color="#37474f", linewidth=2.0, alpha=0.7, label="5-day SMA"),
]
ax.legend(handles=legend_handles, fontsize=16, loc="upper right", framealpha=0.9, edgecolor="none", facecolor="#fafafa")

# Axis limits with padding
y_min, y_max = df["low"].min(), df["high"].max()
y_pad = (y_max - y_min) * 0.12
ax.set_ylim(y_min - y_pad, y_max + y_pad)
x_min = mdates.date2num(df["date"].min())
x_max = mdates.date2num(df["date"].max())
ax.set_xlim(x_min - 1, x_max + 1)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
