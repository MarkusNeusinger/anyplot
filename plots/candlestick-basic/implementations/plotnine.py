"""pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 86/100 | Updated: 2026-02-24
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
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


# Data - 30 trading days of simulated stock prices
np.random.seed(42)
n_days = 30

dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Generate realistic OHLC data with random walk
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

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes})

# Derived columns for plotting
df["day"] = np.arange(len(df))
df["direction"] = pd.Categorical(
    np.where(df["close"] >= df["open"], "Bullish", "Bearish"), categories=["Bullish", "Bearish"]
)
df["body_top"] = df[["open", "close"]].max(axis=1)
df["body_bottom"] = df[["open", "close"]].min(axis=1)

# Date labels for x-axis (show every 5th trading day)
tick_indices = list(range(0, n_days, 5))
tick_labels = [dates[i].strftime("%b %d") for i in tick_indices]

# Palette: blue for bullish, amber for bearish (colorblind-safe)
palette = {"Bullish": "#2196F3", "Bearish": "#FF6F00"}
edge_palette = {"Bullish": "#1565C0", "Bearish": "#E65100"}

# Key reference prices for storytelling
open_first = df["open"].iloc[0]
close_last = df["close"].iloc[-1]

# Plot - candlestick with segments (wicks) and rectangles (bodies)
plot = (
    ggplot(df)
    # Reference line at period opening price
    + geom_hline(yintercept=open_first, linetype="dashed", color="#BBBBBB", size=0.5)
    # Wicks colored by direction for visual coherence
    + geom_segment(aes(x="day", xend="day", y="low", yend="high", color="direction"), size=0.8)
    # Candle bodies with colored edge for definition
    + geom_rect(
        aes(
            xmin="day - 0.35",
            xmax="day + 0.35",
            ymin="body_bottom",
            ymax="body_top",
            fill="direction",
            color="direction",
        ),
        size=0.3,
    )
    + scale_fill_manual(values=palette, name="Direction")
    + scale_color_manual(values=edge_palette, guide=None)
    # Annotate reference line at right edge
    + annotate(
        "text", x=n_days - 0.5, y=open_first + 0.7, label=f"Open ${open_first:.0f}", size=9, color="#999999", ha="right"
    )
    # Annotate net change in clear space
    + annotate(
        "text",
        x=n_days - 0.5,
        y=df["low"].min() - 0.5,
        label=f"Close ${close_last:.0f}  ({(close_last - open_first) / open_first * 100:+.1f}%)",
        size=9,
        color="#E65100",
        ha="right",
    )
    # Axes
    + scale_x_continuous(breaks=tick_indices, labels=tick_labels, expand=(0.02, 0.5))
    + scale_y_continuous(labels=lambda vals: [f"${v:,.0f}" for v in vals])
    + coord_cartesian(ylim=(df["low"].min() - 3, df["high"].max() + 2.5))
    + labs(x="", y="Price ($)", title="candlestick-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, weight="bold"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#d0d0d0", size=0.4, alpha=0.4),
        panel_grid_minor_y=element_blank(),
        legend_position="top",
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_background=element_rect(fill="white", color="none"),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
