""" pyplots.ai
candlestick-basic: Basic Candlestick Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 86/100 | Updated: 2026-02-24
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_line,
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
df["direction"] = np.where(df["close"] >= df["open"], "up", "down")
df["body_top"] = df[["open", "close"]].max(axis=1)
df["body_bottom"] = df[["open", "close"]].min(axis=1)

# Date labels for x-axis (show every 5th trading day)
tick_indices = list(range(0, n_days, 5))
tick_labels = [dates[i].strftime("%b %d") for i in tick_indices]

# Palette: blue for bullish, amber for bearish (colorblind-safe)
palette = {"up": "#2196F3", "down": "#FF6F00"}
edge_palette = {"up": "#1565C0", "down": "#E65100"}

# Plot - candlestick with segments (wicks) and rectangles (bodies)
plot = (
    ggplot(df)
    # Wicks (high-low lines)
    + geom_segment(aes(x="day", xend="day", y="low", yend="high"), color="#555555", size=0.7)
    # Candle bodies with subtle edge for definition
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
    + scale_fill_manual(values=palette, guide=None)
    + scale_color_manual(values=edge_palette, guide=None)
    # Date labels on x-axis
    + scale_x_continuous(breaks=tick_indices, labels=tick_labels, expand=(0.02, 0.5))
    + scale_y_continuous(labels=lambda vals: [f"${v:,.0f}" for v in vals])
    + coord_cartesian(ylim=(df["low"].min() - 1.5, df["high"].max() + 1.5))
    + labs(x="", y="Price ($)", title="candlestick-basic · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#d0d0d0", size=0.4, alpha=0.4),
        panel_grid_minor_y=element_blank(),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
