""" anyplot.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: plotnine 0.15.5 | Python 3.13.13
Quality: 86/100 | Updated: 2026-06-08
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


# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — 8 hues, theme-independent, hybrid-v3 sort
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Conventional green/red for candlesticks — semantic exception (finance: up/down)
BULL_COLOR = "#2E7D32"
BEAR_COLOR = "#C62828"

# Data: 200 trading days of simulated ACME Corp stock prices
np.random.seed(42)
n_days = 200

dates = pd.date_range(start="2023-06-01", periods=n_days, freq="B")

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

senkou_a = (df["tenkan_sen"] + df["kijun_sen"]) / 2
senkou_b_raw = (df["high"].rolling(window=52).max() + df["low"].rolling(window=52).min()) / 2

# Chikou Span: close shifted 26 periods back
df["chikou_span"] = df["close"].shift(-26)

# Integer day index for plotting
df["day"] = np.arange(n_days)

df["body_top"] = df[["open", "close"]].max(axis=1)
df["body_bottom"] = df[["open", "close"]].min(axis=1)
df["candle_fill"] = np.where(df["close"] >= df["open"], BULL_COLOR, BEAR_COLOR)

# Cloud DataFrame shifted 26 periods ahead
cloud_df = pd.DataFrame(
    {"day": np.arange(n_days) + 26, "span_a": senkou_a.values, "span_b": senkou_b_raw.values}
).dropna()

cloud_df["cloud_top"] = np.maximum(cloud_df["span_a"], cloud_df["span_b"])
cloud_df["cloud_bottom"] = np.minimum(cloud_df["span_a"], cloud_df["span_b"])

visible_start = 52
df_vis = df[df["day"] >= visible_start].copy()

# Indicator lines in long format — Imprint palette assignments
# Tenkan-sen → Imprint #1 (brand green), Kijun-sen → Imprint #2 (lavender)
# Chikou Span → Imprint #7 (rose), Senkou A → Imprint #4 (ochre), Senkou B → Imprint #5 (red)
indicator_colors = {
    "Tenkan-sen": IMPRINT_PALETTE[0],  # #009E73 brand green
    "Kijun-sen": IMPRINT_PALETTE[1],  # #C475FD lavender
    "Chikou Span": IMPRINT_PALETTE[6],  # #954477 rose
    "Senkou Span A": IMPRINT_PALETTE[3],  # #BD8233 ochre
    "Senkou Span B": IMPRINT_PALETTE[4],  # #AE3030 matte red
}

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

visible_end = n_days + 26
cloud_vis = cloud_df[(cloud_df["day"] >= visible_start) & (cloud_df["day"] <= visible_end)].copy()

# TK crossover markers for data storytelling
tk_data = df[["day", "tenkan_sen", "kijun_sen"]].dropna().query("day >= @visible_start").copy()
tk_data["tk_diff"] = tk_data["tenkan_sen"] - tk_data["kijun_sen"]
tk_data["prev_diff"] = tk_data["tk_diff"].shift(1)
crossovers = tk_data[(tk_data["tk_diff"] * tk_data["prev_diff"]) < 0].copy()
crossovers["cross_price"] = (crossovers["tenkan_sen"] + crossovers["kijun_sen"]) / 2

# X-axis ticks every ~20 trading days
tick_indices = list(range(visible_start, n_days, 20))
tick_labels = [dates[i].strftime("%b '%y") for i in tick_indices]

plot = (
    ggplot()
    # Kumo cloud — bullish (Span A > Span B): green tint
    + geom_ribbon(
        aes(x="day", ymin="cloud_bottom", ymax="cloud_top"),
        data=cloud_vis[cloud_vis["span_a"] >= cloud_vis["span_b"]],
        fill=BULL_COLOR,
        alpha=0.38,
    )
    # Kumo cloud — bearish (Span B > Span A): red tint
    + geom_ribbon(
        aes(x="day", ymin="cloud_bottom", ymax="cloud_top"),
        data=cloud_vis[cloud_vis["span_a"] < cloud_vis["span_b"]],
        fill=BEAR_COLOR,
        alpha=0.38,
    )
    # Candlestick wicks
    + geom_segment(
        aes(x="day", xend="day", y="low", yend="high"),
        data=df_vis[df_vis["close"] >= df_vis["open"]],
        color="#1B5E20",
        size=0.6,
    )
    + geom_segment(
        aes(x="day", xend="day", y="low", yend="high"),
        data=df_vis[df_vis["close"] < df_vis["open"]],
        color="#8E0000",
        size=0.6,
    )
    # Candlestick bodies
    + geom_rect(
        aes(xmin="day - 0.42", xmax="day + 0.42", ymin="body_bottom", ymax="body_top", fill="candle_fill"),
        data=df_vis[df_vis["close"] >= df_vis["open"]],
        color="#1B5E20",
        size=0.25,
    )
    + geom_rect(
        aes(xmin="day - 0.42", xmax="day + 0.42", ymin="body_bottom", ymax="body_top", fill="candle_fill"),
        data=df_vis[df_vis["close"] < df_vis["open"]],
        color="#8E0000",
        size=0.25,
    )
    # TK crossover markers
    + geom_point(
        aes(x="day", y="cross_price"),
        data=crossovers,
        shape="D",
        size=2.5,
        color=INK,
        fill="#DDCC77",  # Imprint amber — warning/signal role
        stroke=0.5,
    )
    # Indicator lines with legend
    + geom_line(aes(x="day", y="value", color="indicator"), data=lines_long, size=1.1)
    + scale_fill_identity()
    + scale_color_manual(values=indicator_colors, name="Ichimoku Indicators", breaks=list(indicator_colors.keys()))
    + guides(color=guide_legend(override_aes={"size": 2.5}))
    + scale_x_continuous(breaks=tick_indices, labels=tick_labels, expand=(0.01, 0))
    + scale_y_continuous(labels=lambda vals: [f"${v:,.0f}" for v in vals])
    + labs(x="", y="Price ($)", title="indicator-ichimoku · python · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, family="sans-serif", color=INK_SOFT),
        axis_title_y=element_text(size=10, color=INK, margin={"r": 8}),
        axis_title_x=element_blank(),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(margin={"t": 4}),
        plot_title=element_text(size=12, weight="bold", color=INK, margin={"b": 8}),
        legend_title=element_text(size=8, weight="bold", color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.4),
        legend_key_size=12,
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.2, alpha=0.15),
        panel_grid_minor_y=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color="none"),
        plot_margin=0.02,
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
