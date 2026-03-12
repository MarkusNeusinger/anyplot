""" pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-12
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
    geom_point,
    geom_rect,
    geom_ribbon,
    geom_segment,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - 200 trading days of simulated ACME Corp stock prices
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

# Use integer day index for plotting
df["day"] = np.arange(n_days)

# Colorblind-friendly palette
BULL_COLOR = "#0077BB"  # Blue for bullish
BEAR_COLOR = "#CC6633"  # Orange-brown for bearish

# Candlestick columns
df["body_top"] = df[["open", "close"]].max(axis=1)
df["body_bottom"] = df[["open", "close"]].min(axis=1)
df["candle_fill"] = np.where(df["close"] >= df["open"], BULL_COLOR, BEAR_COLOR)

# Build cloud DataFrame shifted 26 periods ahead
cloud_df = pd.DataFrame(
    {"day": np.arange(n_days) + 26, "span_a": senkou_a.values, "span_b": senkou_b_raw.values}
).dropna()

cloud_df["cloud_top"] = np.maximum(cloud_df["span_a"], cloud_df["span_b"])
cloud_df["cloud_bottom"] = np.minimum(cloud_df["span_a"], cloud_df["span_b"])

# Build long-format indicator lines DataFrame using idiomatic pd.concat
visible_start = 52
df_vis = df[df["day"] >= visible_start].copy()

lines_long = pd.concat(
    [
        df[["day", "tenkan_sen"]]
        .dropna()
        .query("day >= @visible_start")
        .rename(columns={"tenkan_sen": "value"})
        .assign(indicator="Tenkan-sen"),
        df[["day", "kijun_sen"]]
        .dropna()
        .query("day >= @visible_start")
        .rename(columns={"kijun_sen": "value"})
        .assign(indicator="Kijun-sen"),
        df[["day", "chikou_span"]]
        .dropna()
        .query("day >= @visible_start")
        .rename(columns={"chikou_span": "value"})
        .assign(indicator="Chikou Span"),
        cloud_df[["day", "span_a"]]
        .query("day >= @visible_start")
        .rename(columns={"span_a": "value"})
        .assign(indicator="Senkou Span A"),
        cloud_df[["day", "span_b"]]
        .query("day >= @visible_start")
        .rename(columns={"span_b": "value"})
        .assign(indicator="Senkou Span B"),
    ],
    ignore_index=True,
)

# Indicator color mapping
indicator_colors = {
    "Tenkan-sen": "#1976D2",
    "Kijun-sen": "#D84315",
    "Chikou Span": "#7B1FA2",
    "Senkou Span A": "#2E7D32",
    "Senkou Span B": "#F9A825",
}

visible_end = n_days + 26
cloud_vis = cloud_df[(cloud_df["day"] >= visible_start) & (cloud_df["day"] <= visible_end)].copy()

# Find TK crossover points for storytelling emphasis
tk_data = df[["day", "tenkan_sen", "kijun_sen"]].dropna().query("day >= @visible_start").copy()
tk_data["tk_diff"] = tk_data["tenkan_sen"] - tk_data["kijun_sen"]
tk_data["prev_diff"] = tk_data["tk_diff"].shift(1)
crossovers = tk_data[(tk_data["tk_diff"] * tk_data["prev_diff"]) < 0].copy()
crossovers["cross_price"] = (crossovers["tenkan_sen"] + crossovers["kijun_sen"]) / 2
crossovers["cross_type"] = np.where(crossovers["tk_diff"] > 0, "bullish", "bearish")

# X-axis tick labels (show every ~20 trading days)
tick_indices = list(range(visible_start, n_days, 20))
tick_labels = [dates[i].strftime("%b '%y") for i in tick_indices]

# Plot
plot = (
    ggplot()
    # Cloud (Kumo) - bullish fill (increased alpha for visibility)
    + geom_ribbon(
        aes(x="day", ymin="cloud_bottom", ymax="cloud_top"),
        data=cloud_vis[cloud_vis["span_a"] >= cloud_vis["span_b"]],
        fill=BULL_COLOR,
        alpha=0.25,
    )
    # Cloud (Kumo) - bearish fill
    + geom_ribbon(
        aes(x="day", ymin="cloud_bottom", ymax="cloud_top"),
        data=cloud_vis[cloud_vis["span_a"] < cloud_vis["span_b"]],
        fill=BEAR_COLOR,
        alpha=0.25,
    )
    # Candlestick wicks - darker for contrast
    + geom_segment(
        aes(x="day", xend="day", y="low", yend="high"),
        data=df_vis[df_vis["close"] >= df_vis["open"]],
        color="#004477",
        size=0.8,
    )
    + geom_segment(
        aes(x="day", xend="day", y="low", yend="high"),
        data=df_vis[df_vis["close"] < df_vis["open"]],
        color="#993300",
        size=0.8,
    )
    # Candlestick bodies
    + geom_rect(
        aes(xmin="day - 0.42", xmax="day + 0.42", ymin="body_bottom", ymax="body_top", fill="candle_fill"),
        data=df_vis[df_vis["close"] >= df_vis["open"]],
        color="#004477",
        size=0.3,
    )
    + geom_rect(
        aes(xmin="day - 0.42", xmax="day + 0.42", ymin="body_bottom", ymax="body_top", fill="candle_fill"),
        data=df_vis[df_vis["close"] < df_vis["open"]],
        color="#993300",
        size=0.3,
    )
    # TK crossover markers - focal points for data storytelling
    + geom_point(
        aes(x="day", y="cross_price"), data=crossovers, shape="D", size=4, color="#222222", fill="#FFDD00", stroke=0.5
    )
    # Indicator lines with mapped color aesthetic for legend
    + geom_line(aes(x="day", y="value", color="indicator"), data=lines_long, size=1.2)
    + scale_fill_identity()
    + scale_color_manual(values=indicator_colors, name="Ichimoku Indicators", breaks=list(indicator_colors.keys()))
    + guides(color=guide_legend(override_aes={"size": 3}))
    + scale_x_continuous(breaks=tick_indices, labels=tick_labels, expand=(0.01, 0))
    + scale_y_continuous(labels=lambda vals: [f"${v:,.0f}" for v in vals])
    + labs(x="", y="Price ($)", title="indicator-ichimoku \u00b7 plotnine \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, family="sans-serif"),
        axis_title_y=element_text(size=20, margin={"r": 12}),
        axis_text=element_text(size=16),
        axis_text_x=element_text(margin={"t": 6}),
        plot_title=element_text(size=24, weight="bold", margin={"b": 12}),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_background=element_rect(fill="white", color="#aaaaaa", size=0.5),
        legend_key_size=20,
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color="#d0d0d0", size=0.3, alpha=0.5),
        panel_grid_minor_y=element_blank(),
        plot_background=element_rect(fill="white", color="none"),
        panel_background=element_rect(fill="#FAFAFA", color="none"),
        plot_margin=0.02,
    )
)

plot.save("plot.png", dpi=300, verbose=False)
