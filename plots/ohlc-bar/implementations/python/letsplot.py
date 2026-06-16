""" anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_line,
    element_rect,
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

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette for up/down
UP_COLOR = "#009E73"  # Brand green (position 1)
DOWN_COLOR = "#AE3030"  # imprint red — down bars

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

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=RULE, size=0.3),
    panel_grid_major_x=element_line(color=RULE, size=0.3),
    axis_title=element_text(size=20, color=INK),
    axis_text=element_text(size=16, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=24, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=16, color=INK_SOFT),
    legend_title=element_text(size=18, color=INK),
)

plot = (
    ggplot()
    # High-Low vertical line
    + geom_segment(aes(x="date", y="low", xend="date", yend="high", color="direction"), data=df, size=1.2)
    # Open tick (left)
    + geom_segment(aes(x="date_left", y="open", xend="date", yend="open", color="direction"), data=df, size=1.5)
    # Close tick (right)
    + geom_segment(aes(x="date", y="close", xend="date_right", yend="close", color="direction"), data=df, size=1.5)
    + scale_color_manual(values={"up": UP_COLOR, "down": DOWN_COLOR}, name="Direction")
    + scale_x_datetime(format="%b %d")
    + labs(title="ohlc-bar · letsplot · anyplot.ai", x="Date", y="Price (USD)")
    + theme_minimal()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px) and HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
