"""anyplot.ai
line-timeseries: Time Series Line Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-09
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_x_datetime,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Columns: set these to your table's column names
DATE = "Date"  # role: date
PRICE = "Bitcoin price (USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=["Date"])
np.random.seed(42)
n_days = 365
dates = pd.date_range(start="2023-01-01", periods=n_days, freq="D")
price = 16500.0
prices = []
for i in range(n_days):
    # Trend component: upward over the year, with mid-year dip
    trend = 20000 + 15000 * np.sin(i / n_days * np.pi * 2) + i * 5
    # Volatility: crypto is more volatile than stocks
    volatility = price * (1 + np.random.randn() * 0.035)
    # Mix trend and volatility
    price = 0.7 * trend + 0.3 * volatility
    prices.append(price)

df = pd.DataFrame({DATE: dates, PRICE: prices})

# Plot: reads only df and the constants above
plot = (
    ggplot(df, aes(x=DATE, y=PRICE))
    + geom_line(color=BRAND, size=1.0, alpha=0.9)
    + geom_point(color=BRAND, size=0.6, alpha=0.5)
    + scale_x_datetime(date_breaks="1 month", date_labels="%b")
    + labs(title="line-timeseries · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.10),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.05),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
