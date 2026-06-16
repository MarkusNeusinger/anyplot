""" anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-17
"""

import os

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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# imprint semantic anchors for up/down distinction
UP_COLOR = "#009E73"  # green - up bars
DOWN_COLOR = "#AE3030"  # red - down bars

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
    # Colors: up (Okabe-Ito position 1) and down (Okabe-Ito position 2)
    + scale_color_manual(
        values={"up": UP_COLOR, "down": DOWN_COLOR}, labels={"up": "Up (Close > Open)", "down": "Down (Close < Open)"}
    )
    # X-axis labels - show every 10th date
    + scale_x_continuous(
        breaks=list(range(0, n_days, 10)), labels=[dates[i].strftime("%b %d") for i in range(0, n_days, 10)]
    )
    # Labels
    + labs(title="ohlc-bar · plotnine · anyplot.ai", x="Date", y="Price (USD)", color="Direction")
    # Theme
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_text_x=element_text(size=16, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=16, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major=element_line(color=INK, alpha=0.10, size=0.3),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color=None),
        plot_background=element_rect(fill=PAGE_BG, color=None),
        axis_line=element_line(color=INK_SOFT, size=0.5),
    )
)

# Save the plot
plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)
