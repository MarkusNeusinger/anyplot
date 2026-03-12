"""pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: altair 6.0.0 | Python 3.14.3
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Simulated 200 days of stock price data with Ichimoku components
np.random.seed(42)
n_days = 200

dates = pd.date_range("2024-01-01", periods=n_days, freq="B")

# Generate realistic price series with trending behavior
returns = np.random.normal(0.001, 0.018, n_days)
returns[40:70] += 0.004  # Strong uptrend
returns[100:130] -= 0.005  # Downtrend
returns[150:180] += 0.003  # Recovery
price = 150 * np.cumprod(1 + returns)

# Build OHLC from close prices
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

# Calculate Ichimoku components (9, 26, 52 periods)
period_9_high = df["high"].rolling(window=9).max()
period_9_low = df["low"].rolling(window=9).min()
period_26_high = df["high"].rolling(window=26).max()
period_26_low = df["low"].rolling(window=26).min()
period_52_high = df["high"].rolling(window=52).max()
period_52_low = df["low"].rolling(window=52).min()

df["tenkan_sen"] = (period_9_high + period_9_low) / 2
df["kijun_sen"] = (period_26_high + period_26_low) / 2

# Senkou Spans are plotted 26 periods ahead
senkou_a = ((df["tenkan_sen"] + df["kijun_sen"]) / 2).values
senkou_b = ((period_52_high + period_52_low) / 2).values

# Chikou Span is the close shifted 26 periods back
chikou = df["close"].values

# Build the extended date range for the 26-period forward shift
future_dates = pd.date_range(start=dates[-1] + pd.tseries.offsets.BDay(1), periods=26, freq="B")
all_dates = dates.append(future_dates)

# Create Senkou Span dataframe (shifted 26 periods forward)
senkou_dates = all_dates[26 : 26 + n_days]
senkou_df = pd.DataFrame({"date": senkou_dates, "senkou_span_a": senkou_a, "senkou_span_b": senkou_b}).dropna()

# Create Chikou Span dataframe (shifted 26 periods back)
chikou_df = pd.DataFrame({"date": dates[: n_days - 26], "chikou_span": chikou[26:]})

# Candlestick direction
df["direction"] = np.where(df["close"] >= df["open"], "Bullish", "Bearish")

# Trim to where we have valid Ichimoku data (after 52 periods)
display_df = df.iloc[52:].copy()

# Cloud coloring: split into bullish/bearish segments
senkou_df["cloud_type"] = np.where(
    senkou_df["senkou_span_a"] >= senkou_df["senkou_span_b"], "Bullish Cloud", "Bearish Cloud"
)

# Y-axis range
all_values = pd.concat([display_df[["high", "low"]].stack(), senkou_df[["senkou_span_a", "senkou_span_b"]].stack()])
y_min = all_values.min() * 0.98
y_max = all_values.max() * 1.02
y_scale = alt.Scale(domain=[y_min, y_max])

# X-axis range (include future for senkou spans)
x_scale = alt.Scale(domain=[display_df["date"].min(), senkou_df["date"].max()])

# Shared x encoding
x_enc = alt.X("date:T", title="Date", scale=x_scale, axis=alt.Axis(format="%b '%y", labelAngle=-45, tickCount="month"))

# Cloud fill - bullish (green tint)
bullish_cloud = senkou_df[senkou_df["cloud_type"] == "Bullish Cloud"]
cloud_bullish = (
    alt.Chart(bullish_cloud)
    .mark_area(opacity=0.18, interpolate="monotone")
    .encode(
        x=x_enc,
        y=alt.Y("senkou_span_a:Q", title="Price ($)", scale=y_scale),
        y2="senkou_span_b:Q",
        color=alt.value("#26A69A"),
    )
)

# Cloud fill - bearish (red/pink tint)
bearish_cloud = senkou_df[senkou_df["cloud_type"] == "Bearish Cloud"]
cloud_bearish = (
    alt.Chart(bearish_cloud)
    .mark_area(opacity=0.18, interpolate="monotone")
    .encode(x=x_enc, y=alt.Y("senkou_span_a:Q", scale=y_scale), y2="senkou_span_b:Q", color=alt.value("#E57373"))
)

# Candlestick wicks
candle_color = alt.Scale(domain=["Bullish", "Bearish"], range=["#26A69A", "#E65100"])
wicks = (
    alt.Chart(display_df)
    .mark_rule(strokeWidth=1.2)
    .encode(
        x=x_enc,
        y=alt.Y("low:Q", scale=y_scale),
        y2="high:Q",
        color=alt.Color("direction:N", scale=candle_color, legend=None),
    )
)

# Candlestick bodies - increased size for better visibility
bodies = (
    alt.Chart(display_df)
    .mark_bar(size=10)
    .encode(
        x=x_enc,
        y=alt.Y("open:Q", scale=y_scale),
        y2="close:Q",
        color=alt.Color("direction:N", scale=candle_color, legend=None),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("open:Q", title="Open", format="$.2f"),
            alt.Tooltip("high:Q", title="High", format="$.2f"),
            alt.Tooltip("low:Q", title="Low", format="$.2f"),
            alt.Tooltip("close:Q", title="Close", format="$.2f"),
        ],
    )
)

# Build long-format dataframe for indicator lines (enables auto-legend)
chikou_display = chikou_df[chikou_df["date"] >= display_df["date"].min()].copy()

lines_tenkan = display_df[["date", "tenkan_sen"]].rename(columns={"tenkan_sen": "value"})
lines_tenkan["component"] = "Tenkan-sen (9)"
lines_kijun = display_df[["date", "kijun_sen"]].rename(columns={"kijun_sen": "value"})
lines_kijun["component"] = "Kijun-sen (26)"
lines_chikou = chikou_display[["date", "chikou_span"]].rename(columns={"chikou_span": "value"})
lines_chikou["component"] = "Chikou Span"
lines_span_a = senkou_df[["date", "senkou_span_a"]].rename(columns={"senkou_span_a": "value"})
lines_span_a["component"] = "Senkou Span A"
lines_span_b = senkou_df[["date", "senkou_span_b"]].rename(columns={"senkou_span_b": "value"})
lines_span_b["component"] = "Senkou Span B"

indicator_df = pd.concat([lines_tenkan, lines_kijun, lines_chikou, lines_span_a, lines_span_b], ignore_index=True)

# Distinct color palette: Kijun-sen now deep orange (#E65100), Senkou Span B warm brown (#8D6E63)
indicator_color = alt.Scale(
    domain=["Tenkan-sen (9)", "Kijun-sen (26)", "Chikou Span", "Senkou Span A", "Senkou Span B"],
    range=["#306998", "#E65100", "#AB47BC", "#26A69A", "#8D6E63"],
)
indicator_dash = alt.Scale(
    domain=["Tenkan-sen (9)", "Kijun-sen (26)", "Chikou Span", "Senkou Span A", "Senkou Span B"],
    range=[[1, 0], [8, 4], [4, 3], [1, 0], [1, 0]],
)

# Nearest-point selection for interactive highlight on indicator lines
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["date"], empty=False)

indicator_lines = (
    alt.Chart(indicator_df)
    .mark_line(strokeWidth=2.2, interpolate="monotone")
    .encode(
        x=x_enc,
        y=alt.Y("value:Q", scale=y_scale),
        color=alt.Color(
            "component:N",
            scale=indicator_color,
            legend=alt.Legend(
                title="Ichimoku Components",
                titleFontSize=16,
                titleFontWeight="bold",
                labelFontSize=16,
                orient="none",
                legendX=1230,
                legendY=8,
                fillColor="rgba(255,255,255,0.92)",
                strokeColor="#bbb",
                padding=12,
                cornerRadius=6,
                symbolStrokeWidth=3,
                symbolSize=220,
                titlePadding=6,
            ),
        ),
        strokeDash=alt.StrokeDash("component:N", scale=indicator_dash, legend=None),
        opacity=alt.value(0.9),
    )
)

# Vertical rule following the cursor for interactive crosshair
crosshair_rule = (
    alt.Chart(indicator_df)
    .mark_rule(color="#999", strokeWidth=0.8, strokeDash=[3, 3])
    .encode(x="date:T", opacity=alt.condition(nearest, alt.value(0.7), alt.value(0)))
    .add_params(nearest)
)

# Crosshair dots on each indicator line
crosshair_dots = (
    alt.Chart(indicator_df)
    .mark_point(size=60, filled=True)
    .encode(
        x="date:T",
        y=alt.Y("value:Q", scale=y_scale),
        color=alt.Color("component:N", scale=indicator_color, legend=None),
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("component:N", title="Line"),
            alt.Tooltip("value:Q", title="Price", format="$.2f"),
        ],
    )
)

# Find a bullish TK cross for annotation (Tenkan crosses above Kijun)
tk_diff = display_df["tenkan_sen"] - display_df["kijun_sen"]
cross_indices = []
for i in range(1, len(tk_diff)):
    idx = tk_diff.index[i]
    idx_prev = tk_diff.index[i - 1]
    if tk_diff.loc[idx_prev] < 0 and tk_diff.loc[idx] >= 0:
        cross_indices.append(idx)

# Find bearish TK cross too (Tenkan crosses below Kijun)
bearish_cross_indices = []
for i in range(1, len(tk_diff)):
    idx = tk_diff.index[i]
    idx_prev = tk_diff.index[i - 1]
    if tk_diff.loc[idx_prev] >= 0 and tk_diff.loc[idx] < 0:
        bearish_cross_indices.append(idx)

# Annotate bullish and bearish TK crosses for storytelling
annotation_layers = []
if cross_indices:
    cx = cross_indices[0]
    bull_cross = pd.DataFrame(
        {
            "date": [display_df.loc[cx, "date"]],
            "price": [display_df.loc[cx, "tenkan_sen"]],
            "label": ["Bullish TK Cross"],
        }
    )
    annotation_layers.append(
        alt.Chart(bull_cross)
        .mark_point(shape="diamond", size=280, strokeWidth=2.5, filled=False)
        .encode(x=x_enc, y=alt.Y("price:Q", scale=y_scale), color=alt.value("#2E7D32"))
    )
    annotation_layers.append(
        alt.Chart(bull_cross)
        .mark_text(align="left", dx=14, dy=-14, fontSize=15, fontWeight="bold", font="sans-serif")
        .encode(x=x_enc, y=alt.Y("price:Q", scale=y_scale), text="label:N", color=alt.value("#2E7D32"))
    )

if bearish_cross_indices:
    bx = bearish_cross_indices[0]
    bear_cross = pd.DataFrame(
        {
            "date": [display_df.loc[bx, "date"]],
            "price": [display_df.loc[bx, "tenkan_sen"]],
            "label": ["Bearish TK Cross"],
        }
    )
    annotation_layers.append(
        alt.Chart(bear_cross)
        .mark_point(shape="diamond", size=280, strokeWidth=2.5, filled=False)
        .encode(x=x_enc, y=alt.Y("price:Q", scale=y_scale), color=alt.value("#C62828"))
    )
    annotation_layers.append(
        alt.Chart(bear_cross)
        .mark_text(align="left", dx=14, dy=-14, fontSize=15, fontWeight="bold", font="sans-serif")
        .encode(x=x_enc, y=alt.Y("price:Q", scale=y_scale), text="label:N", color=alt.value("#C62828"))
    )

# Layer all components
all_layers = [cloud_bullish, cloud_bearish, wicks, bodies, indicator_lines, crosshair_rule, crosshair_dots]
all_layers.extend(annotation_layers)

chart = (
    alt.layer(*all_layers)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "indicator-ichimoku · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            font="sans-serif",
            subtitle="Ichimoku Kinko Hyo (9, 26, 52) — Tenkan / Kijun / Kumo / Chikou",
            subtitleFontSize=18,
            subtitleColor="#78909C",
            subtitlePadding=6,
        ),
    )
    .resolve_scale(color="independent", strokeDash="independent")
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        gridOpacity=0.12,
        gridColor="#E0E0E0",
        domainColor="#BDBDBD",
        tickColor="#BDBDBD",
    )
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
