"""pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-12
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_rect,
    geom_ribbon,
    geom_segment,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - 200 trading days of simulated stock prices
np.random.seed(42)
n_days = 200

dates = pd.date_range(start="2023-06-01", periods=n_days, freq="B")

# Generate realistic OHLC data with trending random walk
price = 145.0
opens, highs, lows, closes = [], [], [], []

for i in range(n_days):
    open_price = price
    trend = 0.05 * np.sin(2 * np.pi * i / 120)
    change = np.random.randn() * 2.5 + trend
    close_price = open_price + change
    high_price = max(open_price, close_price) + abs(np.random.randn() * 1.2)
    low_price = min(open_price, close_price) - abs(np.random.randn() * 1.2)

    opens.append(open_price)
    highs.append(high_price)
    lows.append(low_price)
    closes.append(close_price)

    price = close_price + np.random.randn() * 0.3

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes})

# Compute Ichimoku components (standard 9, 26, 52 parameters)
high_9 = df["high"].rolling(window=9).max()
low_9 = df["low"].rolling(window=9).min()
df["tenkan_sen"] = (high_9 + low_9) / 2

high_26 = df["high"].rolling(window=26).max()
low_26 = df["low"].rolling(window=26).min()
df["kijun_sen"] = (high_26 + low_26) / 2

# Senkou Span A and B (shifted 26 periods ahead)
senkou_a = (df["tenkan_sen"] + df["kijun_sen"]) / 2
senkou_b_raw = (df["high"].rolling(window=52).max() + df["low"].rolling(window=52).min()) / 2

# Chikou Span (close shifted 26 periods back)
df["chikou_span"] = df["close"].shift(-26)

# Use integer day index for plotting (avoids date alignment complexity)
df["day"] = np.arange(n_days)

# Candlestick columns
df["direction"] = np.where(df["close"] >= df["open"], "up", "down")
df["body_top"] = df[["open", "close"]].max(axis=1)
df["body_bottom"] = df[["open", "close"]].min(axis=1)
df["candle_fill"] = np.where(df["close"] >= df["open"], "#26A69A", "#EF5350")
df["candle_edge"] = np.where(df["close"] >= df["open"], "#00897B", "#C62828")

# Build cloud DataFrame shifted 26 periods ahead
cloud_df = pd.DataFrame(
    {"day": np.arange(n_days) + 26, "span_a": senkou_a.values, "span_b": senkou_b_raw.values}
).dropna()

# Split cloud into bullish (span_a >= span_b) and bearish segments
cloud_df["bullish_top"] = np.maximum(cloud_df["span_a"], cloud_df["span_b"])
cloud_df["bullish_bottom"] = np.minimum(cloud_df["span_a"], cloud_df["span_b"])
cloud_df["cloud_fill"] = np.where(cloud_df["span_a"] >= cloud_df["span_b"], "#26A69A", "#EF5350")

# Ichimoku lines DataFrame (for Tenkan, Kijun, Chikou)
lines_df = df[["day", "tenkan_sen", "kijun_sen", "chikou_span"]].copy()

# Trim to visible range: start from day 52 so all indicators are computed
visible_start = 52
visible_end = n_days + 26
df_vis = df[df["day"] >= visible_start].copy()
cloud_vis = cloud_df[(cloud_df["day"] >= visible_start) & (cloud_df["day"] <= visible_end)].copy()
lines_vis = lines_df[lines_df["day"] >= visible_start].copy()

# X-axis tick labels (show every ~20 trading days)
tick_indices = list(range(visible_start, n_days, 20))
tick_labels = [dates[i].strftime("%b '%y") for i in tick_indices]

# Plot
plot = (
    ggplot()
    # Cloud (Kumo) - bullish fill
    + geom_ribbon(
        aes(x="day", ymin="bullish_bottom", ymax="bullish_top"),
        data=cloud_vis[cloud_vis["span_a"] >= cloud_vis["span_b"]],
        fill="#26A69A",
        alpha=0.25,
    )
    # Cloud (Kumo) - bearish fill
    + geom_ribbon(
        aes(x="day", ymin="bullish_bottom", ymax="bullish_top"),
        data=cloud_vis[cloud_vis["span_a"] < cloud_vis["span_b"]],
        fill="#EF5350",
        alpha=0.25,
    )
    # Cloud boundary lines
    + geom_line(aes(x="day", y="span_a"), data=cloud_vis, color="#26A69A", size=0.4, alpha=0.6)
    + geom_line(aes(x="day", y="span_b"), data=cloud_vis, color="#EF5350", size=0.4, alpha=0.6)
    # Candlestick wicks
    + geom_segment(aes(x="day", xend="day", y="low", yend="high", color="candle_edge"), data=df_vis, size=0.6)
    # Candlestick bodies
    + geom_rect(
        aes(
            xmin="day - 0.35",
            xmax="day + 0.35",
            ymin="body_bottom",
            ymax="body_top",
            fill="candle_fill",
            color="candle_edge",
        ),
        data=df_vis,
        size=0.2,
    )
    # Tenkan-sen (Conversion Line)
    + geom_line(aes(x="day", y="tenkan_sen"), data=lines_vis.dropna(subset=["tenkan_sen"]), color="#1976D2", size=1.0)
    # Kijun-sen (Base Line)
    + geom_line(aes(x="day", y="kijun_sen"), data=lines_vis.dropna(subset=["kijun_sen"]), color="#E65100", size=1.0)
    # Chikou Span (Lagging Span)
    + geom_line(
        aes(x="day", y="chikou_span"),
        data=lines_vis.dropna(subset=["chikou_span"]),
        color="#7B1FA2",
        size=0.7,
        alpha=0.7,
    )
    + scale_fill_identity()
    + scale_color_identity()
    + scale_x_continuous(breaks=tick_indices, labels=tick_labels, expand=(0.01, 0))
    + scale_y_continuous(labels=lambda vals: [f"${v:,.0f}" for v in vals])
    + labs(x="", y="Price ($)", title="indicator-ichimoku · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, weight="bold"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#d0d0d0", size=0.4, alpha=0.3),
        panel_grid_minor_y=element_blank(),
        legend_position="none",
        plot_background=element_rect(fill="white", color="none"),
        panel_background=element_rect(fill="white", color="none"),
    )
)

plot.save("plot.png", dpi=300, verbose=False)
