""" anyplot.ai
candlestick-basic: Basic Candlestick Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-30
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — semantic exception: finance uses green=profit/up, red=loss/down
BULL_COLOR = "#009E73"  # Imprint position 1 — bullish / up
BEAR_COLOR = "#AE3030"  # Imprint position 5 — bearish / down

# Data — simulated 30 trading days of OHLC prices
np.random.seed(42)
n_days = 30

dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

price = 100.0
opens, highs, lows, closes = [], [], [], []

for _ in range(n_days):
    open_price = price
    change = np.random.randn() * 2
    close_price = open_price + change
    high_price = max(open_price, close_price) + abs(np.random.randn()) * 1.5
    low_price = min(open_price, close_price) - abs(np.random.randn()) * 1.5
    opens.append(open_price)
    closes.append(close_price)
    highs.append(high_price)
    lows.append(low_price)
    price = close_price

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes})

# Derived candlestick columns
df["direction"] = np.where(df["close"] >= df["open"], "Bullish", "Bearish")
df["body_low"] = df[["open", "close"]].min(axis=1)
df["body_high"] = df[["open", "close"]].max(axis=1)
df["x"] = range(len(df))
df["xmin"] = df["x"] - 0.35
df["xmax"] = df["x"] + 0.35
df["date_str"] = df["date"].dt.strftime("%b %d")

# 5-day simple moving average
df["sma5"] = df["close"].rolling(window=5).mean()
sma_df = df.dropna(subset=["sma5"]).copy()

# Peak price annotation
peak_idx = int(df["high"].idxmax())
peak_x = df.loc[peak_idx, "x"]
peak_y = df.loc[peak_idx, "high"]
peak_df = pd.DataFrame({"x": [peak_x], "y": [peak_y], "label": [f"Peak ${peak_y:.0f}"]})

# Tick positions: every 5th trading day
tick_pos = list(range(0, n_days, 5))
tick_labels = [dates[i].strftime("%b %d") for i in tick_pos]

# Interactive tooltip template
tip_fmt = (
    layer_tooltips()  # noqa: F405
    .line("@date_str")
    .line("Open|$@open")
    .line("High|$@high")
    .line("Low|$@low")
    .line("Close|$@close")
)

plot = (
    ggplot(df)  # noqa: F405
    # Wicks (high-low lines) — thinner than body
    + geom_segment(  # noqa: F405
        aes(x="x", xend="x", y="low", yend="high", color="direction"),  # noqa: F405
        size=0.7,
        tooltips=tip_fmt,
    )
    # Candle bodies (open-close range)
    + geom_rect(  # noqa: F405
        aes(  # noqa: F405
            xmin="xmin", xmax="xmax", ymin="body_low", ymax="body_high", fill="direction", color="direction"
        ),
        size=0.4,
        tooltips=tip_fmt,
    )
    # 5-day SMA trend line
    + geom_line(  # noqa: F405
        aes(x="x", y="sma5"),  # noqa: F405
        data=sma_df,
        color=INK_MUTED,
        size=0.8,
        alpha=0.7,
        linetype="dashed",
        tooltips="none",
    )
    # Peak diamond marker
    + geom_point(  # noqa: F405
        aes(x="x", y="y"),  # noqa: F405
        data=peak_df,
        size=4,
        shape=18,
        color=INK,
    )
    # Peak label
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=peak_df,
        size=4,
        color=INK,
        nudge_y=1.8,
        fontface="bold",
    )
    + scale_fill_manual(values={"Bullish": BULL_COLOR, "Bearish": BEAR_COLOR})  # noqa: F405
    + scale_color_manual(values={"Bullish": BULL_COLOR, "Bearish": BEAR_COLOR})  # noqa: F405
    + scale_x_continuous(breaks=tick_pos, labels=tick_labels, expand=[0.02, 0])  # noqa: F405
    + scale_y_continuous(expand=[0.14, 0])  # noqa: F405  — headroom for peak label
    + labs(  # noqa: F405
        x="Trading Day (Jan–Feb 2024)",
        y="Price ($)",
        title="candlestick-basic · python · letsplot · anyplot.ai",
        subtitle="Simulated 30-day equity prices — 5-day moving average (dashed)",
        color="",
        fill="",
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=16, color=INK, face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=11, color=INK_SOFT),  # noqa: F405
        axis_title=element_text(size=12, color=INK),  # noqa: F405
        axis_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        legend_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        legend_title=element_text(size=10, color=INK),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405  — y-only grid for financial chart
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.2),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),  # noqa: F405
        legend_position="right",
    )
    + ggsize(800, 450)  # noqa: F405  — scaled 4× on export → 3200 × 1800 px
)

# Save — theme-suffixed outputs (pipeline runs this script twice)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)  # noqa: F405  → 3200 × 1800 px
ggsave(plot, f"plot-{THEME}.html", path=".")  # noqa: F405
