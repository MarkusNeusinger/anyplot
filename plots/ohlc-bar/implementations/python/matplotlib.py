""" anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-17
"""

import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# imprint semantic anchors
COLOR_UP = "#009E73"  # green — up bars
COLOR_DOWN = "#AE3030"  # red — down bars

# Data - Generate 45 trading days of synthetic stock OHLC data
np.random.seed(42)
n_days = 45

# Start from a base price and simulate random walk with some trend
base_price = 150.0
dates = pd.bdate_range(start="2024-06-01", periods=n_days)

# Generate price movements
returns = np.random.normal(0.001, 0.02, n_days)  # Daily returns with slight upward bias
cumulative_returns = np.cumprod(1 + returns)
close_prices = base_price * cumulative_returns

# Generate OHLC data with realistic intraday ranges
high_add = np.random.uniform(0.5, 3.0, n_days)
low_sub = np.random.uniform(0.5, 3.0, n_days)

# Open is close of previous day (with small gap)
open_prices = np.roll(close_prices, 1) * (1 + np.random.uniform(-0.005, 0.005, n_days))
open_prices[0] = base_price

# High and low must encompass open and close
high_prices = np.maximum(open_prices, close_prices) + high_add
low_prices = np.minimum(open_prices, close_prices) - low_sub

# Create DataFrame
df = pd.DataFrame({"date": dates, "open": open_prices, "high": high_prices, "low": low_prices, "close": close_prices})

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Draw OHLC bars
tick_width = 0.4  # Width of open/close ticks in days
line_width = 2.0

for _idx, row in df.iterrows():
    date_num = mdates.date2num(row["date"])

    # Determine color based on price direction
    color = COLOR_UP if row["close"] >= row["open"] else COLOR_DOWN

    # Draw high-low vertical line
    ax.plot([date_num, date_num], [row["low"], row["high"]], color=color, linewidth=line_width, solid_capstyle="round")

    # Draw open tick (left side)
    ax.plot(
        [date_num - tick_width, date_num],
        [row["open"], row["open"]],
        color=color,
        linewidth=line_width,
        solid_capstyle="butt",
    )

    # Draw close tick (right side)
    ax.plot(
        [date_num, date_num + tick_width],
        [row["close"], row["close"]],
        color=color,
        linewidth=line_width,
        solid_capstyle="butt",
    )

# Style
ax.set_xlabel("Date", fontsize=20, color=INK)
ax.set_ylabel("Price (USD)", fontsize=20, color=INK)
ax.set_title("ohlc-bar · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Format x-axis dates
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MONDAY))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_minor_locator(mdates.DayLocator())
fig.autofmt_xdate(rotation=45)

# Spine styling
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
for spine in ("left", "bottom"):
    ax.spines[spine].set_color(INK_SOFT)

# Grid for reading price levels
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.xaxis.grid(True, alpha=0.08, linewidth=0.8, color=INK)

# Add padding to y-axis
y_min, y_max = ax.get_ylim()
y_padding = (y_max - y_min) * 0.05
ax.set_ylim(y_min - y_padding, y_max + y_padding)

# Add legend for up/down bars
legend_elements = [
    Line2D([0], [0], color=COLOR_UP, linewidth=3, label="Up (Close ≥ Open)"),
    Line2D([0], [0], color=COLOR_DOWN, linewidth=3, label="Down (Close < Open)"),
]
legend = ax.legend(handles=legend_elements, fontsize=16, loc="upper left")
legend.get_frame().set_facecolor(ELEVATED_BG)
legend.get_frame().set_edgecolor(INK_SOFT)
for text in legend.get_texts():
    text.set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
