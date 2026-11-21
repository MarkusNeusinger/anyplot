""" anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 for up days, position 5 (red) for down days
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open"  # role: open
HIGH = "High"  # role: high
LOW = "Low"  # role: low
CLOSE = "Close"  # role: close
VOLUME = "Volume (shares)"  # role: volume

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=["Date"])
np.random.seed(42)
n_days = 60
returns = np.random.normal(0.001, 0.025, n_days)
returns[15] = -0.08  # dramatic drop
returns[35] = 0.06  # strong bounce
returns[45] = -0.05  # another reversal
close_prices = 150 * np.cumprod(1 + returns)
open_prices = np.roll(close_prices, 1)
open_prices[0] = 150
high_prices = np.maximum(open_prices, close_prices) * (1 + np.abs(np.random.normal(0, 0.012, n_days)))
low_prices = np.minimum(open_prices, close_prices) * (1 - np.abs(np.random.normal(0, 0.012, n_days)))
volatility = np.abs(close_prices - open_prices) / open_prices
volume = (5_000_000 * (1 + volatility * 10 + np.random.uniform(-0.3, 0.3, n_days))).astype(int)

df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-02", periods=n_days, freq="B"),
        OPEN: open_prices,
        HIGH: high_prices,
        LOW: low_prices,
        CLOSE: close_prices,
        VOLUME: volume,
    }
)

# Plot: reads only df and the constants above
DIRECTION = "Direction"
POSITION = "Trading day"
plot_df = df.copy()
plot_df[POSITION] = np.arange(len(df))
plot_df[DIRECTION] = np.where(df[CLOSE] >= df[OPEN], "Up", "Down")
direction_colors = {"Up": IMPRINT_PALETTE[0], "Down": IMPRINT_PALETTE[4]}

# Shared x-axis: one tick every 10 trading days, labelled with the date
date_breaks = list(range(0, len(df), 10))
date_labels = [df[DATE].iloc[i].strftime("%b %d") for i in date_breaks]
x_axis_title = f"{DATE} ({df[DATE].iloc[0].year})"

vol_min, vol_max = df[VOLUME].min(), df[VOLUME].max()
vol_breaks = [int(vol_min), int((vol_min + vol_max) / 2), int(vol_max)]
vol_labels = [f"{v / 1_000_000:.1f}M" for v in vol_breaks]

# Style
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major=element_line(color=INK_SOFT, size=0.15),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT, size=0.15),
    plot_title=element_text(color=INK, size=16),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=11),
)

# Price pane: wick from low to high, body from open to close
candle_plot = (
    ggplot(plot_df)
    + geom_segment(aes(x=POSITION, xend=POSITION, y=LOW, yend=HIGH, color=DIRECTION), size=0.75)
    + geom_segment(aes(x=POSITION, xend=POSITION, y=OPEN, yend=CLOSE, color=DIRECTION), size=3.0)
    + scale_color_manual(values=direction_colors, name=DIRECTION)
    + scale_x_continuous(breaks=date_breaks, labels=date_labels)
    + labs(title="Stock Trading · candlestick-volume · python · letsplot · anyplot.ai", y="Price ($)", x="")
    + anyplot_theme
    + theme(
        axis_text_x=element_blank(),
        legend_position=[0.5, 0.95],
        legend_justification=[0.5, 1.0],
        legend_direction="horizontal",
        plot_margin=[20, 10, 1, 21],
    )
    + ggsize(800, 315)
)

# Volume pane: bars from zero in the same up/down colors
volume_plot = (
    ggplot(plot_df)
    + geom_bar(aes(x=POSITION, y=VOLUME, fill=DIRECTION), stat="identity", width=0.8, color=PAGE_BG, size=0)
    + scale_fill_manual(values=direction_colors, name=DIRECTION)
    + scale_x_continuous(breaks=date_breaks, labels=date_labels)
    + scale_y_continuous(breaks=vol_breaks, labels=vol_labels)
    + labs(x=x_axis_title, y=VOLUME)
    + anyplot_theme
    + theme(legend_position="none", plot_margin=[1, 10, 5, 5])
    + ggsize(800, 135)
)

combined = gggrid([candle_plot, volume_plot], ncol=1, heights=[0.7, 0.3], hspace=0, vspace=0) + ggsize(800, 450)

# Save outputs
ggsave(combined, f"plot-{THEME}.png", scale=4, path=".")
ggsave(combined, f"plot-{THEME}.html", path=".")
