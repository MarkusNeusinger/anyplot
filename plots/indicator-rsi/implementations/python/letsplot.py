"""anyplot.ai
indicator-rsi: RSI Technical Indicator Chart
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-05-16
"""
# ruff: noqa: F405

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Generate realistic stock price data and calculate RSI
np.random.seed(42)

n_days = 120
dates = pd.date_range("2024-06-01", periods=n_days, freq="B")

# Generate volatile price movements to demonstrate overbought/oversold zones
returns = np.random.normal(0.0005, 0.025, n_days)  # Increased volatility
price = 150 * np.exp(np.cumsum(returns))

# Calculate RSI with 14-period lookback
period = 14
delta = np.diff(price)
gains = np.where(delta > 0, delta, 0)
losses = np.where(delta < 0, -delta, 0)

# Calculate average gains/losses using exponential moving average
avg_gain = np.zeros(len(delta))
avg_loss = np.zeros(len(delta))

avg_gain[period - 1] = np.mean(gains[:period])
avg_loss[period - 1] = np.mean(losses[:period])

for i in range(period, len(delta)):
    avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i]) / period
    avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i]) / period

rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100)
rsi = 100 - (100 / (1 + rs))

# Align RSI with dates (first period-1 values are NaN)
rsi_values = np.full(n_days, np.nan)
rsi_values[period:] = rsi[period - 1 :]

df = pd.DataFrame({"date": dates, "rsi": rsi_values}).dropna()

df["date_num"] = range(len(df))

# Create zones for shading
overbought_df = pd.DataFrame(
    {"xmin": [df["date_num"].min()], "xmax": [df["date_num"].max()], "ymin": [70], "ymax": [100]}
)

oversold_df = pd.DataFrame({"xmin": [df["date_num"].min()], "xmax": [df["date_num"].max()], "ymin": [0], "ymax": [30]})

# Create the RSI chart with theme-adaptive styling
plot = (
    ggplot()
    # Overbought zone
    + geom_rect(
        data=overbought_df, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill="#DC2626", alpha=0.1
    )
    # Oversold zone
    + geom_rect(
        data=oversold_df, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), fill="#16A34A", alpha=0.1
    )
    # Horizontal threshold lines
    + geom_hline(yintercept=70, color="#DC2626", size=1.2, linetype="dashed")
    + geom_hline(yintercept=30, color="#16A34A", size=1.2, linetype="dashed")
    + geom_hline(yintercept=50, color=INK_SOFT, size=0.8, linetype="dotted")
    # RSI line in brand color
    + geom_line(data=df, mapping=aes(x="date_num", y="rsi"), color=BRAND, size=1.8)
    # Labels and styling
    + labs(title="indicator-rsi · letsplot · anyplot.ai", x="Trading Day", y="RSI (14-period)")
    + scale_y_continuous(limits=[0, 100], breaks=[0, 30, 50, 70, 100])
    + scale_x_continuous(breaks=[0, 25, 50, 75, 100], labels=["Jun", "Jul", "Aug", "Sep", "Oct"])
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK_SOFT, size=0.4),
        panel_grid_minor=element_blank(),
        axis_line=element_line(color=INK_SOFT, size=0.5),
        plot_title=element_text(size=24, face="bold", color=INK),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
    )
    + ggsize(1600, 900)
)

# Save as PNG (scale 3x for 4800 × 2700 px)
ggsave(plot, f"plot-{THEME}.png", scale=3)

# Save as HTML for interactive viewing
ggsave(plot, f"plot-{THEME}.html")
