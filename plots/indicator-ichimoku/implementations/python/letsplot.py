""" anyplot.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 92/100 | Updated: 2026-06-08
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()  # noqa: F405

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — semantic exception: profit/loss maps to green/red
BULL_COLOR = "#009E73"  # Imprint green — bullish candles
BEAR_COLOR = "#AE3030"  # Imprint matte red — bearish candles
TENKAN_COLOR = "#C475FD"  # Imprint lavender (position 2) — Tenkan-sen
KIJUN_COLOR = "#4467A3"  # Imprint blue (position 3) — Kijun-sen
CHIKOU_COLOR = "#BD8233"  # Imprint ochre (position 4) — Chikou Span
SIGNAL_COLOR = "#DDCC77"  # Imprint amber — TK Crossover signal marker

# Data — 200 trading days of simulated OHLC with Ichimoku components
np.random.seed(42)
n_days = 200

dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Generate realistic OHLC via random walk
price = 150.0
opens, highs, lows, closes = [], [], [], []
for _ in range(n_days):
    open_price = price
    change = np.random.randn() * 2.5
    close_price = open_price + change
    high_price = max(open_price, close_price) + abs(np.random.randn()) * 1.5
    low_price = min(open_price, close_price) - abs(np.random.randn()) * 1.5
    opens.append(open_price)
    closes.append(close_price)
    highs.append(high_price)
    lows.append(low_price)
    price = close_price

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes})

# Compute Ichimoku components (standard parameters: 9, 26, 52)
high_s = df["high"]
low_s = df["low"]

tenkan_sen = (high_s.rolling(9).max() + low_s.rolling(9).min()) / 2
kijun_sen = (high_s.rolling(26).max() + low_s.rolling(26).min()) / 2
senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
senkou_span_b = ((high_s.rolling(52).max() + low_s.rolling(52).min()) / 2).shift(26)
chikou_span = df["close"].shift(-26)

df["tenkan_sen"] = tenkan_sen
df["kijun_sen"] = kijun_sen
df["senkou_span_a"] = senkou_span_a
df["senkou_span_b"] = senkou_span_b
df["chikou_span"] = chikou_span

# Numeric x-axis for precise candlestick positioning
df["x"] = range(len(df))

# Candlestick geometry columns
df["direction"] = np.where(df["close"] >= df["open"], "Bullish", "Bearish")
df["body_low"] = df[["open", "close"]].min(axis=1)
df["body_high"] = df[["open", "close"]].max(axis=1)
df["xmin"] = df["x"] - 0.35
df["xmax"] = df["x"] + 0.35

# Visible range (skip first 52 rows for full lookback)
visible_start = 52
df_visible = df.iloc[visible_start:].copy()

# Cloud data — split by bullish/bearish polarity for color-coded fill
df_cloud = df_visible.dropna(subset=["senkou_span_a", "senkou_span_b"]).copy()
df_cloud_bull = df_cloud[df_cloud["senkou_span_a"] >= df_cloud["senkou_span_b"]].copy()
df_cloud_bear = df_cloud[df_cloud["senkou_span_a"] < df_cloud["senkou_span_b"]].copy()

# Indicator line data (dropped NaN for clean line rendering)
df_tenkan = df_visible.dropna(subset=["tenkan_sen"]).copy()
df_kijun = df_visible.dropna(subset=["kijun_sen"]).copy()
df_chikou = df_visible.dropna(subset=["chikou_span"]).copy()

# X-axis ticks (every 20 trading days)
tick_pos = list(range(visible_start, len(df), 20))
tick_labels = [dates[i].strftime("%b %d") for i in tick_pos if i < len(dates)]
tick_pos = tick_pos[: len(tick_labels)]

# Tooltip columns
df_visible["date_str"] = df_visible["date"].dt.strftime("%b %d, %Y")
df_visible["change_pct"] = ((df_visible["close"] - df_visible["open"]) / df_visible["open"] * 100).round(2)

# Tenkan/Kijun crossover signal points
df_visible["tk_cross"] = (df_visible["tenkan_sen"] > df_visible["kijun_sen"]) != (
    df_visible["tenkan_sen"].shift(1) > df_visible["kijun_sen"].shift(1)
)
df_crossovers = df_visible[df_visible["tk_cross"] & df_visible["tenkan_sen"].notna()].copy()

tip_fmt = (
    layer_tooltips()  # noqa: F405
    .title("@date_str")
    .line("Open|$@{open}")
    .line("High|$@{high}")
    .line("Low|$@{low}")
    .line("Close|$@{close}")
    .line("Change|@{change_pct}%")
    .format("open", ".2f")
    .format("high", ".2f")
    .format("low", ".2f")
    .format("close", ".2f")
)

tenkan_tip = (
    layer_tooltips()  # noqa: F405
    .title("Tenkan-sen")
    .line("Value|$@{tenkan_sen}")
    .format("tenkan_sen", ".2f")
)
kijun_tip = (
    layer_tooltips()  # noqa: F405
    .title("Kijun-sen")
    .line("Value|$@{kijun_sen}")
    .format("kijun_sen", ".2f")
)

# Title (51 chars — under 67 baseline, default size=16)
title = "indicator-ichimoku · python · letsplot · anyplot.ai"
subtitle = "Ichimoku Kinko Hyo — Kumo shifts green→red as trend reverses mid-year; amber diamonds mark TK crossovers"

# Plot
plot = (
    ggplot()  # noqa: F405
    # Kumo cloud — bullish segment (green)
    + geom_ribbon(  # noqa: F405
        aes(x="x", ymin="senkou_span_b", ymax="senkou_span_a"),  # noqa: F405
        data=df_cloud_bull,
        fill=BULL_COLOR,
        alpha=0.15,
        tooltips="none",
    )
    # Kumo cloud — bearish segment (red)
    + geom_ribbon(  # noqa: F405
        aes(x="x", ymin="senkou_span_a", ymax="senkou_span_b"),  # noqa: F405
        data=df_cloud_bear,
        fill=BEAR_COLOR,
        alpha=0.15,
        tooltips="none",
    )
    # Senkou Span A boundary line
    + geom_line(  # noqa: F405
        aes(x="x", y="senkou_span_a"),  # noqa: F405
        data=df_cloud,
        color=BULL_COLOR,
        size=0.6,
        alpha=0.5,
        tooltips="none",
    )
    # Senkou Span B boundary line
    + geom_line(  # noqa: F405
        aes(x="x", y="senkou_span_b"),  # noqa: F405
        data=df_cloud,
        color=BEAR_COLOR,
        size=0.6,
        alpha=0.5,
        tooltips="none",
    )
    # Candlestick wicks
    + geom_segment(  # noqa: F405
        aes(x="x", xend="x", y="low", yend="high", color="direction"),  # noqa: F405
        data=df_visible,
        size=0.7,
        tooltips=tip_fmt,
    )
    # Candlestick bodies
    + geom_rect(  # noqa: F405
        aes(xmin="xmin", xmax="xmax", ymin="body_low", ymax="body_high", fill="direction", color="direction"),  # noqa: F405
        data=df_visible,
        size=0.4,
        tooltips=tip_fmt,
    )
    # Tenkan-sen (conversion line)
    + geom_line(  # noqa: F405
        aes(x="x", y="tenkan_sen"),  # noqa: F405
        data=df_tenkan,
        color=TENKAN_COLOR,
        size=1.2,
        tooltips=tenkan_tip,
        manual_key=layer_key("Tenkan-sen"),  # noqa: F405
    )
    # Kijun-sen (base line)
    + geom_line(  # noqa: F405
        aes(x="x", y="kijun_sen"),  # noqa: F405
        data=df_kijun,
        color=KIJUN_COLOR,
        size=1.2,
        tooltips=kijun_tip,
        manual_key=layer_key("Kijun-sen"),  # noqa: F405
    )
    # Chikou Span (lagging line — shifted 26 bars back)
    + geom_line(  # noqa: F405
        aes(x="x", y="chikou_span"),  # noqa: F405
        data=df_chikou,
        color=CHIKOU_COLOR,
        size=1.0,
        alpha=0.85,
        linetype="dashed",
        tooltips="none",
        manual_key=layer_key("Chikou Span"),  # noqa: F405
    )
    # TK Crossover signal markers
    + geom_point(  # noqa: F405
        aes(x="x", y="tenkan_sen"),  # noqa: F405
        data=df_crossovers,
        color=SIGNAL_COLOR,
        fill=SIGNAL_COLOR,
        size=5,
        shape=23,
        stroke=1.5,
        tooltips=layer_tooltips().title("TK Crossover").line("@date_str"),  # noqa: F405
        manual_key=layer_key("TK Crossover"),  # noqa: F405
    )
    # Scales
    + scale_fill_manual(values={"Bullish": BULL_COLOR, "Bearish": BEAR_COLOR})  # noqa: F405
    + scale_color_manual(values={"Bullish": BULL_COLOR, "Bearish": BEAR_COLOR})  # noqa: F405
    + scale_x_continuous(breaks=tick_pos, labels=tick_labels, expand=[0.02, 0])  # noqa: F405
    + labs(x="Trading Day (2024)", y="Price ($)", title=title, subtitle=subtitle)  # noqa: F405
    + guides(fill="none", color="none")  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
        axis_title=element_text(size=12, color=INK),  # noqa: F405
        axis_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        plot_title=element_text(size=16, color=INK, face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=11, color=INK_SOFT, face="italic"),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color=INK, size=0.3),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
        legend_position=[0.05, 0.95],
        legend_justification=[0.0, 1.0],
        legend_title=element_text(size=10, face="bold", color=INK),  # noqa: F405
        legend_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),  # noqa: F405
    )
    + ggsize(800, 450)  # noqa: F405
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)  # noqa: F405
ggsave(plot, f"plot-{THEME}.html", path=".")  # noqa: F405
