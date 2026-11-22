""" anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-22
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

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP_COLOR = IMPRINT_PALETTE[0]  # up bars
DOWN_COLOR = IMPRINT_PALETTE[4]  # down bars

# Constants
TICK_WIDTH = 0.3  # open/close tick length in bar spacings

# Columns
DATE = "date"  # role: date
OPEN = "open"  # role: open
HIGH = "high"  # role: high
LOW = "low"  # role: low
CLOSE = "close"  # role: close

# Data
np.random.seed(42)
n_days = 50
start_price = 150.0
returns = np.random.normal(0.001, 0.02, n_days)
close_prices = start_price * np.cumprod(1 + returns)
open_prices = np.roll(close_prices, 1)
open_prices[0] = start_price
daily_volatility = np.abs(np.random.normal(0, 0.015, n_days))
high_prices = np.maximum(open_prices, close_prices) * (1 + daily_volatility)
low_prices = np.minimum(open_prices, close_prices) * (1 - daily_volatility)
df = pd.DataFrame(
    {
        DATE: pd.bdate_range(start="2024-06-01", periods=n_days),
        OPEN: open_prices,
        HIGH: high_prices,
        LOW: low_prices,
        CLOSE: close_prices,
    }
)

# Plot
DAY, DIRECTION, OPEN_X, CLOSE_X = "day_num", "direction", "open_x_start", "close_x_end"
df[DAY] = np.arange(len(df))
df[DIRECTION] = np.where(df[CLOSE] >= df[OPEN], "up", "down")
df[OPEN_X] = df[DAY] - TICK_WIDTH
df[CLOSE_X] = df[DAY] + TICK_WIDTH
label_step = max(len(df) // 5, 1)
label_pos = list(range(0, len(df), label_step))
label_text = [df[DATE].iloc[i].strftime("%b %d") for i in label_pos]
plot = (
    ggplot(df)
    + geom_segment(aes(x=DAY, xend=DAY, y=LOW, yend=HIGH, color=DIRECTION), size=0.9)
    + geom_segment(aes(x=OPEN_X, xend=DAY, y=OPEN, yend=OPEN, color=DIRECTION), size=0.9)
    + geom_segment(aes(x=DAY, xend=CLOSE_X, y=CLOSE, yend=CLOSE, color=DIRECTION), size=0.9)
    + scale_color_manual(
        values=[UP_COLOR, DOWN_COLOR], limits=["up", "down"], labels=["Up (Close > Open)", "Down (Close < Open)"]
    )
    + scale_x_continuous(breaks=label_pos, labels=label_text)
    + labs(title="ohlc-bar · python · plotnine · anyplot.ai", x="Date", y="Price (USD)", color="Direction")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, weight="bold", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_key=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        panel_grid_major=element_line(color=INK, alpha=0.10, size=0.3),
        panel_grid_minor=element_blank(),
        panel_background=element_rect(fill=PAGE_BG, color=None),
        plot_background=element_rect(fill=PAGE_BG, color=None),
        axis_line=element_line(color=INK_SOFT, size=0.5),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
