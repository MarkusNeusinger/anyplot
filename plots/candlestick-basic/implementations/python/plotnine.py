"""anyplot.ai
candlestick-basic: Basic Candlestick Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-30
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens (Imprint palette + adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — semantic exception: green=bullish (gain), red=bearish (loss)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BULL_COLOR = IMPRINT_PALETTE[0]
BEAR_COLOR = IMPRINT_PALETTE[4]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open ($)"  # role: open
HIGH = "High ($)"  # role: high
LOW = "Low ($)"  # role: low
CLOSE = "Close ($)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 30
price = 150.0
opens, highs, lows, closes = [], [], [], []
for _ in range(n_days):
    open_price = price
    change = np.random.randn() * 3
    close_price = open_price + change
    high_price = max(open_price, close_price) + abs(np.random.randn() * 1.5)
    low_price = min(open_price, close_price) - abs(np.random.randn() * 1.5)
    opens.append(open_price)
    highs.append(high_price)
    lows.append(low_price)
    closes.append(close_price)
    price = close_price + np.random.randn() * 0.5

df = pd.DataFrame(
    {
        DATE: pd.date_range(start="2024-01-02", periods=n_days, freq="B"),
        OPEN: opens,
        HIGH: highs,
        LOW: lows,
        CLOSE: closes,
    }
)

# Plot: reads only df and the constants above
candles = df.assign(
    day=np.arange(len(df)),
    body_top=df[[OPEN, CLOSE]].max(axis=1),
    body_bottom=df[[OPEN, CLOSE]].min(axis=1),
    direction=pd.Categorical(np.where(df[CLOSE] >= df[OPEN], "Bullish", "Bearish"), categories=["Bullish", "Bearish"]),
)
palette = {"Bullish": BULL_COLOR, "Bearish": BEAR_COLOR}

# X-axis tick labels (every 5th trading day)
tick_indices = list(range(0, len(df), 5))
tick_labels = [df[DATE].iloc[i].strftime("%b %d") for i in tick_indices]

# Title size shrinks for long titles (12pt up to 67 characters)
title = "candlestick-basic · python · plotnine · anyplot.ai"
title_size = max(8, round(12 * 67 / len(title)))

plot = (
    ggplot(candles)
    # Wicks colored by direction
    + geom_segment(aes(x="day", xend="day", y=LOW, yend=HIGH, color="direction"), size=0.8)
    # Candle bodies — fill by direction, INK_SOFT edge for definition
    + geom_rect(
        aes(xmin="day - 0.35", xmax="day + 0.35", ymin="body_bottom", ymax="body_top", fill="direction"),
        color=INK_SOFT,
        size=0.3,
    )
    + scale_fill_manual(values=palette, name="Direction")
    + scale_color_manual(values=palette, guide=None)
    + scale_x_continuous(breaks=tick_indices, labels=tick_labels, expand=(0.02, 0.5))
    + scale_y_continuous(labels=lambda vals: [f"${v:,.0f}" for v in vals])
    + coord_cartesian(ylim=(df[LOW].min() - 2, df[HIGH].max() + 2))
    + labs(x="", y="Price ($)", title=title)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7),
        plot_title=element_text(size=title_size, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3, alpha=0.15),
        panel_grid_minor_y=element_blank(),
        axis_line=element_line(color=INK_SOFT),
        legend_position="top",
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
