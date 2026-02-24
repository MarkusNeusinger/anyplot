""" pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-24
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()  # noqa: F405

# Data - simulated 30 trading days of stock OHLC data
np.random.seed(42)
n_days = 30

dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Generate realistic OHLC data with random walk
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

# Candlestick properties
df["direction"] = np.where(df["close"] >= df["open"], "Bullish", "Bearish")
df["body_low"] = df[["open", "close"]].min(axis=1)
df["body_high"] = df[["open", "close"]].max(axis=1)
df["x"] = range(len(df))
df["xmin"] = df["x"] - 0.35
df["xmax"] = df["x"] + 0.35
df["date_str"] = df["date"].dt.strftime("%b %d")

# 5-day simple moving average for trend storytelling
df["sma5"] = df["close"].rolling(window=5).mean()
sma_df = df.dropna(subset=["sma5"]).copy()

# Peak price focal point
peak_idx = int(df["high"].idxmax())
peak_x = df.loc[peak_idx, "x"]
peak_y = df.loc[peak_idx, "high"]
peak_df = pd.DataFrame({"x": [peak_x], "y": [peak_y], "label": [f"Peak ${peak_y:.0f}"]})

bull_color = "#2271B5"  # Blue for bullish (up)
bear_color = "#D55E00"  # Orange for bearish (down) — colorblind-safe
sma_color = "#555555"

# Tick label positions: every 5th trading day
tick_pos = list(range(0, n_days, 5))
tick_labels = [dates[i].strftime("%b %d") for i in tick_pos]

# Tooltip template for interactive HTML export
tip_fmt = (
    layer_tooltips()  # noqa: F405
    .line("@date_str")
    .line("Open|$@open")
    .line("High|$@high")
    .line("Low|$@low")
    .line("Close|$@close")
)

# Plot — unified color mapping for bull/bear direction
plot = (
    ggplot(df)  # noqa: F405
    # Wicks (high-low lines) colored by direction
    + geom_segment(  # noqa: F405
        aes(x="x", xend="x", y="low", yend="high", color="direction"),  # noqa: F405
        size=0.9,
        tooltips=tip_fmt,
    )
    # Candle bodies colored by direction
    + geom_rect(  # noqa: F405
        aes(  # noqa: F405
            xmin="xmin", xmax="xmax", ymin="body_low", ymax="body_high", fill="direction", color="direction"
        ),
        size=0.5,
        tooltips=tip_fmt,
    )
    # 5-day SMA trend line — guides the viewer through the price narrative
    + geom_line(  # noqa: F405
        aes(x="x", y="sma5"),  # noqa: F405
        data=sma_df,
        color=sma_color,
        size=1.0,
        alpha=0.55,
        linetype="dashed",
        tooltips="none",
    )
    # Peak annotation — focal point for storytelling
    + geom_point(  # noqa: F405
        aes(x="x", y="y"),  # noqa: F405
        data=peak_df,
        size=6,
        shape=18,
        color="#222222",
    )
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=peak_df,
        size=13,
        color="#222222",
        nudge_y=1.8,
        fontface="bold",
    )
    + scale_fill_manual(values={"Bullish": bull_color, "Bearish": bear_color})  # noqa: F405
    + scale_color_manual(values={"Bullish": bull_color, "Bearish": bear_color})  # noqa: F405
    + scale_x_continuous(breaks=tick_pos, labels=tick_labels, expand=[0.02, 0])  # noqa: F405
    + scale_y_continuous(expand=[0.12, 0])  # noqa: F405  — room for peak label
    + labs(  # noqa: F405
        x="Trading Day (Jan\u2013Feb 2024)",
        y="Price ($)",
        title="candlestick-basic \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="Simulated 30-day equity prices \u2014 5-day moving average (dashed)",
    )
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        axis_text=element_text(size=16, color="#555555"),  # noqa: F405
        plot_title=element_text(size=24, color="#1a1a1a", face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=17, color="#666666"),  # noqa: F405
        panel_grid_major_x=element_line(color="#ececec", size=0.3),  # noqa: F405
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.4),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="white", color="white"),  # noqa: F405
        legend_position="none",
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)  # noqa: F405
ggsave(plot, "plot.html", path=".")  # noqa: F405
