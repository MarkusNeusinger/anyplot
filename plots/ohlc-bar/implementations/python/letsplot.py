"""anyplot.ai
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
    element_blank,
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
RULE = "#E4E1D8" if THEME == "light" else "#33332E"  # solid hex: lets-plot ignores rgba alpha in grid colors

# Imprint palette: position 1 for up bars, position 5 (red) for down bars
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP_COLOR = IMPRINT_PALETTE[0]
DOWN_COLOR = IMPRINT_PALETTE[4]

# Constants
TICK_OFFSET = pd.Timedelta(hours=8)  # length of the open / close ticks, shorter than half a trading day

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open (USD/t)"  # role: open
HIGH = "High (USD/t)"  # role: high
LOW = "Low (USD/t)"  # role: low
CLOSE = "Close (USD/t)"  # role: close
DIRECTION = "Direction"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("copper.csv")
# Daily copper futures, a random walk where each open is the prior close
rng = np.random.default_rng(2025)
n_days = 60
dates = pd.date_range("2025-09-01", periods=n_days, freq="B")
returns = rng.normal(0.0004, 0.012, n_days)
ranges = rng.uniform(0.004, 0.016, (n_days, 2))
closes = 9800.0 * np.cumprod(1 + returns)
opens = np.concatenate([[9800.0], closes[:-1]])
df = pd.DataFrame(
    {
        DATE: dates,
        OPEN: opens,
        HIGH: np.maximum(opens, closes) * (1 + ranges[:, 0]),
        LOW: np.minimum(opens, closes) * (1 - ranges[:, 1]),
        CLOSE: closes,
    }
)

# Plot: reads only df and the constants above
df[DIRECTION] = np.where(df[CLOSE] >= df[OPEN], "Up", "Down")
df["date_left"] = df[DATE] - TICK_OFFSET
df["date_right"] = df[DATE] + TICK_OFFSET

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_grid_major_y=element_line(color=RULE, size=0.3),
    panel_grid_major_x=element_line(color=RULE, size=0.3),
    panel_grid_minor=element_blank(),
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(size=16, color=INK),
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(size=10, color=INK_SOFT),
    legend_title=element_text(size=12, color=INK),
)

plot = (
    ggplot(df)
    # High-low vertical line
    + geom_segment(aes(x=DATE, y=LOW, xend=DATE, yend=HIGH, color=DIRECTION), size=0.9)
    # Open tick to the left
    + geom_segment(aes(x="date_left", y=OPEN, xend=DATE, yend=OPEN, color=DIRECTION), size=1.1)
    # Close tick to the right
    + geom_segment(aes(x=DATE, y=CLOSE, xend="date_right", yend=CLOSE, color=DIRECTION), size=1.1)
    + scale_color_manual(values={"Up": UP_COLOR, "Down": DOWN_COLOR}, name=DIRECTION)
    + scale_x_datetime(format="%b %d")
    + labs(title="Copper Futures · ohlc-bar · python · letsplot · anyplot.ai", x=DATE, y="Price (USD per tonne)")
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save as PNG (scale 4x for 3200 × 1800 px) and HTML
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
