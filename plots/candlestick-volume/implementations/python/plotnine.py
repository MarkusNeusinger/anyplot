""" anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: plotnine 0.15.9 | Python 3.14.10
Quality: 80/100 | Updated: 2026-11-21
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
    facet_grid,
    geom_col,
    geom_rect,
    geom_segment,
    ggplot,
    ggsave,
    labs,
    scale_color_manual,
    scale_fill_manual,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP_COLOR = IMPRINT_PALETTE[0]
DOWN_COLOR = IMPRINT_PALETTE[4]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open"  # role: open
HIGH = "High"  # role: high
LOW = "Low"  # role: low
CLOSE = "Close"  # role: close
VOLUME = "Volume"  # role: volume

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=[DATE])
np.random.seed(42)
n_periods = 60
returns = np.random.normal(0.001, 0.02, n_periods)
close_prices = 100 * np.exp(np.cumsum(returns))
open_prices = close_prices * (1 + np.random.normal(0, 0.01, n_periods))
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=n_periods, freq="D"),
        OPEN: open_prices,
        HIGH: np.maximum(open_prices, close_prices) + np.abs(np.random.normal(0, 0.5, n_periods)),
        LOW: np.minimum(open_prices, close_prices) - np.abs(np.random.normal(0, 0.5, n_periods)),
        CLOSE: close_prices,
        VOLUME: np.random.exponential(1e6, n_periods),
    }
)

# Plot
df["direction"] = np.where(df[CLOSE] >= df[OPEN], "Up", "Down")
df["x_min"] = df[DATE] - pd.Timedelta(hours=12)
df["x_max"] = df[DATE] + pd.Timedelta(hours=12)

# One copy of the table per facet pane
df_price = df.assign(pane="Price (OHLC)")
df_volume = df.assign(pane="Trading Volume")

direction_colors = {"Up": UP_COLOR, "Down": DOWN_COLOR}

plot = (
    ggplot()
    # Wicks: low to high
    + geom_segment(
        aes(x=DATE, y=LOW, xend=DATE, yend=HIGH, color="direction"), data=df_price, size=0.5, show_legend=False
    )
    # Bodies: open to close
    + geom_rect(
        aes(xmin="x_min", xmax="x_max", ymin=OPEN, ymax=CLOSE, fill="direction"), data=df_price, show_legend=False
    )
    # Volume bars in the same up/down colors
    + geom_col(aes(x=DATE, y=VOLUME, fill="direction"), data=df_volume, show_legend=False)
    + facet_grid("pane ~ .", scales="free_y")
    + scale_color_manual(values=direction_colors)
    + scale_fill_manual(values=direction_colors)
    + labs(title="candlestick-volume · python · plotnine · anyplot.ai", x=DATE, y="")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.3),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK),
        strip_text_y=element_text(size=9, color=INK),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.2, alpha=0.15),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
    )
)

ggsave(plot, f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
