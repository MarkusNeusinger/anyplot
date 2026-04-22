""" pyplots.ai
ohlc-bar: OHLC Bar Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_text,
    geom_segment,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_color_manual,
    scale_x_datetime,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Data: Generate 50 trading days of OHLC data
np.random.seed(42)
n_days = 50
dates = pd.date_range("2024-06-01", periods=n_days, freq="B")

# Simulate price movements with random walk
price = 150.0
opens, highs, lows, closes = [], [], [], []

for _ in range(n_days):
    daily_return = np.random.normal(0, 0.02)
    daily_volatility = np.random.uniform(0.01, 0.03)

    open_price = price
    close_price = price * (1 + daily_return)
    high_price = max(open_price, close_price) * (1 + daily_volatility)
    low_price = min(open_price, close_price) * (1 - daily_volatility)

    opens.append(open_price)
    highs.append(high_price)
    lows.append(low_price)
    closes.append(close_price)

    price = close_price

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes})

# Add direction for coloring
df["direction"] = np.where(df["close"] >= df["open"], "up", "down")

# Calculate tick offsets (in milliseconds for datetime axis)
tick_offset = pd.Timedelta(hours=8)
df["date_left"] = df["date"] - tick_offset
df["date_right"] = df["date"] + tick_offset

# Build OHLC bar chart using segments
# 1. Vertical line from low to high
# 2. Left tick at open price
# 3. Right tick at close price

plot = (
    ggplot()
    # High-Low vertical line
    + geom_segment(aes(x="date", y="low", xend="date", yend="high", color="direction"), data=df, size=1.2)
    # Open tick (left)
    + geom_segment(aes(x="date_left", y="open", xend="date", yend="open", color="direction"), data=df, size=1.5)
    # Close tick (right)
    + geom_segment(aes(x="date", y="close", xend="date_right", yend="close", color="direction"), data=df, size=1.5)
    + scale_color_manual(values={"up": "#306998", "down": "#DC2626"}, name="Direction")
    + scale_x_datetime(format="%b %d")
    + labs(title="ohlc-bar · letsplot · pyplots.ai", x="Date", y="Price (USD)")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        legend_title=element_text(size=18),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, "plot.png", path=".", scale=3)

# Save as HTML for interactivity
ggsave(plot, "plot.html", path=".")
