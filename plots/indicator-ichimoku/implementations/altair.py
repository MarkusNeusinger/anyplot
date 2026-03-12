""" pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-12
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
x_enc = alt.X("date:T", title="Date", scale=x_scale, axis=alt.Axis(format="%b '%y", labelAngle=-45))

# Cloud fill - bullish (green tint)
bullish_cloud = senkou_df[senkou_df["cloud_type"] == "Bullish Cloud"]
cloud_bullish = (
    alt.Chart(bullish_cloud)
    .mark_area(opacity=0.2)
    .encode(
        x=x_enc,
        y=alt.Y("senkou_span_a:Q", title="Price ($)", scale=y_scale),
        y2="senkou_span_b:Q",
        color=alt.value("#26A69A"),
    )
)

# Cloud fill - bearish (red tint)
bearish_cloud = senkou_df[senkou_df["cloud_type"] == "Bearish Cloud"]
cloud_bearish = (
    alt.Chart(bearish_cloud)
    .mark_area(opacity=0.2)
    .encode(x=x_enc, y=alt.Y("senkou_span_a:Q", scale=y_scale), y2="senkou_span_b:Q", color=alt.value("#EF5350"))
)

# Senkou Span A line
span_a_line = (
    alt.Chart(senkou_df)
    .mark_line(strokeWidth=1.5, opacity=0.6)
    .encode(x=x_enc, y=alt.Y("senkou_span_a:Q", scale=y_scale), color=alt.value("#26A69A"))
)

# Senkou Span B line
span_b_line = (
    alt.Chart(senkou_df)
    .mark_line(strokeWidth=1.5, opacity=0.6)
    .encode(x=x_enc, y=alt.Y("senkou_span_b:Q", scale=y_scale), color=alt.value("#EF5350"))
)

# Candlestick wicks
candle_color = alt.Scale(domain=["Bullish", "Bearish"], range=["#26A69A", "#FF8F00"])
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

# Candlestick bodies
bodies = (
    alt.Chart(display_df)
    .mark_bar(size=8)
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

# Tenkan-sen (Conversion Line - 9 period)
tenkan_line = (
    alt.Chart(display_df)
    .mark_line(strokeWidth=2)
    .encode(x=x_enc, y=alt.Y("tenkan_sen:Q", scale=y_scale), color=alt.value("#306998"))
)

# Kijun-sen (Base Line - 26 period)
kijun_line = (
    alt.Chart(display_df)
    .mark_line(strokeWidth=2, strokeDash=[8, 4])
    .encode(x=x_enc, y=alt.Y("kijun_sen:Q", scale=y_scale), color=alt.value("#FF6F00"))
)

# Chikou Span (Lagging Span - close shifted 26 periods back)
chikou_display = chikou_df[chikou_df["date"] >= display_df["date"].min()]
chikou_line = (
    alt.Chart(chikou_display)
    .mark_line(strokeWidth=1.5, opacity=0.5, strokeDash=[4, 3])
    .encode(x=x_enc, y=alt.Y("chikou_span:Q", scale=y_scale), color=alt.value("#AB47BC"))
)

# Layer all components
chart = (
    alt.layer(
        cloud_bullish, cloud_bearish, span_a_line, span_b_line, wicks, bodies, tenkan_line, kijun_line, chikou_line
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "indicator-ichimoku · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="Ichimoku Kinko Hyo (9, 26, 52) — Tenkan/Kijun/Kumo/Chikou",
            subtitleFontSize=16,
            subtitleColor="#78909C",
        ),
    )
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.15)
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
