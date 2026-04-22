""" pyplots.ai
ohlc-bar: OHLC Bar Chart
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Data - Generate 50 days of realistic stock OHLC data
np.random.seed(42)
n_days = 50
start_price = 150.0

# Generate price movements using random walk
returns = np.random.normal(0.001, 0.02, n_days)
close_prices = start_price * np.cumprod(1 + returns)

# Generate open, high, low based on close
open_prices = np.roll(close_prices, 1)
open_prices[0] = start_price

# High and low are generated around the open-close range
daily_volatility = np.abs(np.random.normal(0, 0.015, n_days))
high_prices = np.maximum(open_prices, close_prices) * (1 + daily_volatility)
low_prices = np.minimum(open_prices, close_prices) * (1 - daily_volatility)

# Create date range (business days)
dates = pd.bdate_range(start="2024-06-01", periods=n_days)

# Create DataFrame
df = pd.DataFrame(
    {
        "date": dates,
        "day_num": range(n_days),
        "open": open_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
    }
)

# Determine bar direction for coloring
df["direction"] = np.where(df["close"] >= df["open"], "up", "down")

# Define tick width for open/close marks
tick_width = 0.3

# Create data for open ticks (extend left from bar)
df["open_x_start"] = df["day_num"] - tick_width
df["open_x_end"] = df["day_num"]

# Create data for close ticks (extend right from bar)
df["close_x_start"] = df["day_num"]
df["close_x_end"] = df["day_num"] + tick_width

# Create the OHLC bar chart
plot = (
    ggplot(df)
    # High-Low vertical line
    + geom_segment(aes(x="day_num", xend="day_num", y="low", yend="high", color="direction"), size=1.2)
    # Open tick (left horizontal line)
    + geom_segment(aes(x="open_x_start", xend="open_x_end", y="open", yend="open", color="direction"), size=1.2)
    # Close tick (right horizontal line)
    + geom_segment(aes(x="close_x_start", xend="close_x_end", y="close", yend="close", color="direction"), size=1.2)
    # Colors: up (green) and down (red)
    + scale_color_manual(
        values={"up": "#2E7D32", "down": "#C62828"}, labels={"up": "Up (Close > Open)", "down": "Down (Close < Open)"}
    )
    # X-axis labels - show every 10th date
    + scale_x_continuous(
        breaks=list(range(0, n_days, 10)), labels=[dates[i].strftime("%b %d") for i in range(0, n_days, 10)]
    )
    # Labels
    + labs(title="ohlc-bar \u00b7 plotnine \u00b7 pyplots.ai", x="Date", y="Price (USD)", color="Direction")
    # Theme
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_line(color="#CCCCCC", alpha=0.3),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill="white"),
        plot_background=element_rect(fill="white"),
    )
)

# Save the plot
plot.save("plot.png", dpi=300, verbose=False)
