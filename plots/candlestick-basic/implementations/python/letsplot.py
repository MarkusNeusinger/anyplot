"""anyplot.ai
candlestick-basic: Basic Candlestick Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: pending | Updated: 2026-05-30
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — semantic exception: finance uses green=profit/up, red=loss/down
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BULL_COLOR = IMPRINT_PALETTE[0]  # Imprint position 1 — bullish / up
BEAR_COLOR = IMPRINT_PALETTE[4]  # Imprint position 5 — bearish / down

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open"  # role: open
HIGH = "High"  # role: high
LOW = "Low"  # role: low
CLOSE = "Close"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 30
price = 100.0
opens, highs, lows, closes = [], [], [], []
for _ in range(n_days):
    open_price = price
    close_price = open_price + np.random.randn() * 2
    highs.append(max(open_price, close_price) + abs(np.random.randn()) * 1.5)
    lows.append(min(open_price, close_price) - abs(np.random.randn()) * 1.5)
    opens.append(open_price)
    closes.append(close_price)
    price = close_price
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
candles = df.copy()
candles["Direction"] = np.where(candles[CLOSE] >= candles[OPEN], "Bullish", "Bearish")
candles["body_low"] = candles[[OPEN, CLOSE]].min(axis=1)
candles["body_high"] = candles[[OPEN, CLOSE]].max(axis=1)
candles["x"] = np.arange(len(candles))
candles["xmin"] = candles["x"] - 0.35
candles["xmax"] = candles["x"] + 0.35
candles["Day"] = candles[DATE].dt.strftime("%b %d")

# Date labels on every 5th trading day
tick_pos = list(range(0, len(candles), 5))
tick_labels = candles["Day"].iloc[tick_pos].tolist()

tip_fmt = (
    layer_tooltips()  # noqa: F405
    .line("@Day")
    .line(f"{OPEN}|$@{OPEN}")
    .line(f"{HIGH}|$@{HIGH}")
    .line(f"{LOW}|$@{LOW}")
    .line(f"{CLOSE}|$@{CLOSE}")
)

price_pad = (candles[HIGH].max() - candles[LOW].min()) * 0.05

plot = (
    ggplot(candles)  # noqa: F405
    # Wicks (low-high lines), thinner than the body
    + geom_segment(  # noqa: F405
        aes(x="x", xend="x", y=LOW, yend=HIGH, color="Direction"),  # noqa: F405
        size=0.7,
        tooltips=tip_fmt,
    )
    # Candle bodies (open-close range)
    + geom_rect(  # noqa: F405
        aes(xmin="xmin", xmax="xmax", ymin="body_low", ymax="body_high", fill="Direction", color="Direction"),  # noqa: F405
        size=0.4,
        tooltips=tip_fmt,
    )
    + scale_fill_manual(values={"Bullish": BULL_COLOR, "Bearish": BEAR_COLOR})  # noqa: F405
    + scale_color_manual(values={"Bullish": BULL_COLOR, "Bearish": BEAR_COLOR})  # noqa: F405
    + scale_x_continuous(breaks=tick_pos, labels=tick_labels, expand=[0.02, 0])  # noqa: F405
    + scale_y_continuous(  # noqa: F405
        limits=[candles[LOW].min() - price_pad, candles[HIGH].max() + price_pad]
    )
    + labs(  # noqa: F405
        x="Trading day (Jan–Feb 2024)",
        y="Price ($)",
        title="candlestick-basic · python · letsplot · anyplot.ai",
        color="",
        fill="",
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=16, color=INK, face="bold"),  # noqa: F405
        axis_title=element_text(size=12, color=INK),  # noqa: F405
        axis_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        legend_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        legend_title=element_text(size=10, color=INK),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color=GRID, size=0.3),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
        legend_position="right",
    )
    + ggsize(800, 450)  # noqa: F405
)

# Save: scaled 4x on export to 3200 x 1800 px
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)  # noqa: F405
ggsave(plot, f"plot-{THEME}.html", path=".")  # noqa: F405
