""" anyplot.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: altair 6.2.1 | Python 3.13.13
Quality: 91/100 | Updated: 2026-06-08
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — semantic exception: finance convention maps bullish→green, bearish→red
BULLISH_COLOR = "#009E73"  # Imprint position 1 — semantic green = up / gain
BEARISH_COLOR = "#AE3030"  # Imprint position 5 — semantic red  = down / loss

# Ichimoku line colors: remaining Imprint positions (positions 1 & 5 reserved semantically above)
LINE_COLORS = {
    "Tenkan-sen (9)": "#C475FD",  # Imprint position 2
    "Kijun-sen (26)": "#4467A3",  # Imprint position 3
    "Chikou Span": "#BD8233",  # Imprint position 4
    "Senkou Span A": "#2ABCCD",  # Imprint position 6
    "Senkou Span B": "#954477",  # Imprint position 7
}

# Data — 200 business days of simulated OHLC with engineered trend phases
np.random.seed(42)
n_days = 200
dates = pd.date_range("2024-01-01", periods=n_days, freq="B")

returns = np.random.normal(0.001, 0.018, n_days)
returns[40:70] += 0.004  # uptrend
returns[100:130] -= 0.005  # downtrend
returns[150:180] += 0.003  # recovery
price = 150 * np.cumprod(1 + returns)

open_prices = np.empty(n_days)
high_prices = np.empty(n_days)
low_prices = np.empty(n_days)
close_prices = price.copy()

open_prices[0] = 150.0
for i in range(1, n_days):
    open_prices[i] = close_prices[i - 1] + np.random.uniform(-0.5, 0.5)

for i in range(n_days):
    spread = np.random.uniform(1, 4)
    high_prices[i] = max(open_prices[i], close_prices[i]) + np.random.uniform(0.5, spread)
    low_prices[i] = min(open_prices[i], close_prices[i]) - np.random.uniform(0.5, spread)

df = pd.DataFrame(
    {
        "date": dates,
        "open": np.round(open_prices, 2),
        "high": np.round(high_prices, 2),
        "low": np.round(low_prices, 2),
        "close": np.round(close_prices, 2),
    }
)

# Ichimoku components — standard (9, 26, 52) parameters
period_9_high = df["high"].rolling(9).max()
period_9_low = df["low"].rolling(9).min()
period_26_high = df["high"].rolling(26).max()
period_26_low = df["low"].rolling(26).min()
period_52_high = df["high"].rolling(52).max()
period_52_low = df["low"].rolling(52).min()

df["tenkan_sen"] = (period_9_high + period_9_low) / 2
df["kijun_sen"] = (period_26_high + period_26_low) / 2

senkou_a = ((df["tenkan_sen"] + df["kijun_sen"]) / 2).values
senkou_b = ((period_52_high + period_52_low) / 2).values

# Senkou Spans shifted 26 periods into the future
future_dates = pd.date_range(start=dates[-1] + pd.tseries.offsets.BDay(1), periods=26, freq="B")
all_dates = dates.append(future_dates)
senkou_dates = all_dates[26 : 26 + n_days]

senkou_df = pd.DataFrame({"date": senkou_dates, "senkou_span_a": senkou_a, "senkou_span_b": senkou_b}).dropna()

# Chikou Span: close shifted 26 periods into the past
chikou_df = pd.DataFrame({"date": dates[: n_days - 26], "chikou_span": close_prices[26:]})

df["direction"] = np.where(df["close"] >= df["open"], "Bullish", "Bearish")

# Display from period 52 onward (52-period lookback complete)
display_df = df.iloc[52:].copy()

senkou_df["cloud_type"] = np.where(
    senkou_df["senkou_span_a"] >= senkou_df["senkou_span_b"], "Bullish Cloud", "Bearish Cloud"
)

# Axis domains
all_prices = pd.concat([display_df[["high", "low"]].stack(), senkou_df[["senkou_span_a", "senkou_span_b"]].stack()])
y_min = all_prices.min() * 0.98
y_max = all_prices.max() * 1.02
y_range = y_max - y_min
y_scale = alt.Scale(domain=[y_min, y_max])
x_scale = alt.Scale(domain=[display_df["date"].min(), senkou_df["date"].max()])

x_enc = alt.X("date:T", title="Date", scale=x_scale, axis=alt.Axis(format="%b '%y", labelAngle=-30, tickCount="month"))

# Cloud — increased opacity (0.28) for clearer boundary visibility
bullish_cloud_data = senkou_df[senkou_df["cloud_type"] == "Bullish Cloud"]
bearish_cloud_data = senkou_df[senkou_df["cloud_type"] == "Bearish Cloud"]

cloud_bullish = (
    alt.Chart(bullish_cloud_data)
    .mark_area(opacity=0.28, interpolate="monotone")
    .encode(
        x=x_enc,
        y=alt.Y("senkou_span_a:Q", title="Price ($)", scale=y_scale),
        y2="senkou_span_b:Q",
        color=alt.value(BULLISH_COLOR),
    )
)

cloud_bearish = (
    alt.Chart(bearish_cloud_data)
    .mark_area(opacity=0.28, interpolate="monotone")
    .encode(x=x_enc, y=alt.Y("senkou_span_a:Q", scale=y_scale), y2="senkou_span_b:Q", color=alt.value(BEARISH_COLOR))
)

# Candlesticks
candle_scale = alt.Scale(domain=["Bullish", "Bearish"], range=[BULLISH_COLOR, BEARISH_COLOR])

wicks = (
    alt.Chart(display_df)
    .mark_rule(strokeWidth=1.1)
    .encode(
        x=x_enc,
        y=alt.Y("low:Q", scale=y_scale),
        y2="high:Q",
        color=alt.Color("direction:N", scale=candle_scale, legend=None),
    )
)

bodies = (
    alt.Chart(display_df)
    .mark_bar(size=2.5)
    .encode(
        x=x_enc,
        y=alt.Y("open:Q", scale=y_scale),
        y2="close:Q",
        color=alt.Color("direction:N", scale=candle_scale, legend=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("open:Q", title="Open", format="$.2f"),
            alt.Tooltip("high:Q", title="High", format="$.2f"),
            alt.Tooltip("low:Q", title="Low", format="$.2f"),
            alt.Tooltip("close:Q", title="Close", format="$.2f"),
        ],
    )
)

# Indicator lines — long-format for auto-legend
chikou_display = chikou_df[chikou_df["date"] >= display_df["date"].min()].copy()

comp_names = list(LINE_COLORS.keys())
comp_colors = list(LINE_COLORS.values())

lines_tenkan = (
    display_df[["date", "tenkan_sen"]].rename(columns={"tenkan_sen": "value"}).assign(component="Tenkan-sen (9)")
)
lines_kijun = (
    display_df[["date", "kijun_sen"]].rename(columns={"kijun_sen": "value"}).assign(component="Kijun-sen (26)")
)
lines_chikou = (
    chikou_display[["date", "chikou_span"]].rename(columns={"chikou_span": "value"}).assign(component="Chikou Span")
)
lines_span_a = (
    senkou_df[["date", "senkou_span_a"]].rename(columns={"senkou_span_a": "value"}).assign(component="Senkou Span A")
)
lines_span_b = (
    senkou_df[["date", "senkou_span_b"]].rename(columns={"senkou_span_b": "value"}).assign(component="Senkou Span B")
)

indicator_df = pd.concat([lines_tenkan, lines_kijun, lines_chikou, lines_span_a, lines_span_b], ignore_index=True)

indicator_color_scale = alt.Scale(domain=comp_names, range=comp_colors)
indicator_dash_scale = alt.Scale(domain=comp_names, range=[[1, 0], [8, 4], [4, 3], [1, 0], [1, 0]])

nearest = alt.selection_point(nearest=True, on="pointerover", fields=["date"], empty=False)

indicator_lines = (
    alt.Chart(indicator_df)
    .mark_line(strokeWidth=2.0, interpolate="monotone")
    .encode(
        x=x_enc,
        y=alt.Y("value:Q", scale=y_scale),
        color=alt.Color(
            "component:N",
            scale=indicator_color_scale,
            legend=alt.Legend(
                title="Ichimoku Components",
                titleFontSize=12,
                titleFontWeight="bold",
                labelFontSize=11,
                orient="none",
                legendX=318,
                legendY=5,
                fillColor=ELEVATED_BG,
                strokeColor=INK_SOFT,
                labelColor=INK_SOFT,
                titleColor=INK,
                padding=8,
                cornerRadius=4,
                symbolStrokeWidth=2.5,
                symbolSize=140,
                titlePadding=4,
            ),
        ),
        strokeDash=alt.StrokeDash("component:N", scale=indicator_dash_scale, legend=None),
        opacity=alt.value(0.9),
    )
)

# Interactive crosshair
crosshair_rule = (
    alt.Chart(indicator_df)
    .mark_rule(color=INK_MUTED, strokeWidth=0.8, strokeDash=[3, 3])
    .encode(x="date:T", opacity=alt.condition(nearest, alt.value(0.7), alt.value(0)))
    .add_params(nearest)
)

crosshair_dots = (
    alt.Chart(indicator_df)
    .mark_point(size=60, filled=True)
    .encode(
        x="date:T",
        y=alt.Y("value:Q", scale=y_scale),
        color=alt.Color("component:N", scale=indicator_color_scale, legend=None),
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("component:N", title="Line"),
            alt.Tooltip("value:Q", title="Price", format="$.2f"),
        ],
    )
)

# TK crossover annotations — positioned with clearance above/below the candles
tk_diff = display_df["tenkan_sen"] - display_df["kijun_sen"]
bull_cross_idx = []
bear_cross_idx = []
for i in range(1, len(tk_diff)):
    idx = tk_diff.index[i]
    idx_prev = tk_diff.index[i - 1]
    if tk_diff.loc[idx_prev] < 0 and tk_diff.loc[idx] >= 0:
        bull_cross_idx.append(idx)
    elif tk_diff.loc[idx_prev] >= 0 and tk_diff.loc[idx] < 0:
        bear_cross_idx.append(idx)

annotation_layers = []
if bull_cross_idx:
    cx = bull_cross_idx[0]
    bull_df = pd.DataFrame(
        {
            "date": [display_df.loc[cx, "date"]],
            "price": [display_df.loc[cx, "high"] + y_range * 0.055],
            "label": ["▲ TK Cross"],
        }
    )
    annotation_layers.append(
        alt.Chart(bull_df)
        .mark_text(align="center", fontSize=11, fontWeight="bold")
        .encode(x=x_enc, y=alt.Y("price:Q", scale=y_scale), text="label:N", color=alt.value(BULLISH_COLOR))
    )

if bear_cross_idx:
    bx = bear_cross_idx[0]
    bear_df = pd.DataFrame(
        {
            "date": [display_df.loc[bx, "date"]],
            "price": [display_df.loc[bx, "low"] - y_range * 0.055],
            "label": ["▼ TK Cross"],
        }
    )
    annotation_layers.append(
        alt.Chart(bear_df)
        .mark_text(align="center", fontSize=11, fontWeight="bold")
        .encode(x=x_enc, y=alt.Y("price:Q", scale=y_scale), text="label:N", color=alt.value(BEARISH_COLOR))
    )

# Title — length 49 chars, below 67-char baseline, no scaling needed
title_str = "indicator-ichimoku · python · altair · anyplot.ai"
n_title = len(title_str)
ratio = 67 / n_title if n_title > 67 else 1.0
title_fontsize = max(11, round(16 * ratio))

# Compose all layers
all_layers = [cloud_bullish, cloud_bearish, wicks, bodies, indicator_lines, crosshair_rule, crosshair_dots]
all_layers.extend(annotation_layers)

chart = (
    alt.layer(*all_layers)
    .properties(
        width=620,
        height=320,
        background=PAGE_BG,
        title=alt.Title(
            title_str,
            fontSize=title_fontsize,
            anchor="middle",
            font="sans-serif",
            color=INK,
            subtitle="Ichimoku Kinko Hyo (9, 26, 52) — Tenkan / Kijun / Kumo / Chikou",
            subtitleFontSize=11,
            subtitleColor=INK_MUTED,
            subtitlePadding=4,
        ),
    )
    .resolve_scale(color="independent", strokeDash="independent")
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0.5)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        gridOpacity=0.12,
        gridColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save PNG — pad to exact 3200 × 1800 target
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

# Save HTML (interactive)
chart.save(f"plot-{THEME}.html")
