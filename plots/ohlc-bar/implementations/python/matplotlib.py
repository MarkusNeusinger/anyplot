""" pyplots.ai
ohlc-bar: OHLC Bar Chart
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-08
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


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
fig, ax = plt.subplots(figsize=(16, 9))

# Draw OHLC bars
tick_width = 0.4  # Width of open/close ticks in days
line_width = 2.0

for _idx, row in df.iterrows():
    date_num = mdates.date2num(row["date"])

    # Determine color based on price direction
    if row["close"] >= row["open"]:
        color = "#306998"  # Python Blue for up bars
    else:
        color = "#D62728"  # Red for down bars

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

# Styling
ax.set_xlabel("Date", fontsize=20)
ax.set_ylabel("Price (USD)", fontsize=20)
ax.set_title("ohlc-bar · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)

# Format x-axis dates
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MONDAY))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.xaxis.set_minor_locator(mdates.DayLocator())
fig.autofmt_xdate(rotation=45)

# Grid for reading price levels
ax.grid(True, alpha=0.3, linestyle="--", axis="y")
ax.grid(True, alpha=0.15, linestyle="--", axis="x")

# Add padding to y-axis
y_min, y_max = ax.get_ylim()
y_padding = (y_max - y_min) * 0.05
ax.set_ylim(y_min - y_padding, y_max + y_padding)

# Add legend for up/down bars
legend_elements = [
    Line2D([0], [0], color="#306998", linewidth=3, label="Up (Close ≥ Open)"),
    Line2D([0], [0], color="#D62728", linewidth=3, label="Down (Close < Open)"),
]
ax.legend(handles=legend_elements, fontsize=16, loc="upper left")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
