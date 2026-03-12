""" pyplots.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-12
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - 200 trading days of simulated stock prices
np.random.seed(42)
n_days = 200
dates = pd.date_range(start="2023-06-01", periods=n_days, freq="B")

price = 150.0
drift = np.concatenate(
    [np.full(50, 0.15), np.full(40, -0.10), np.full(30, 0.25), np.full(40, -0.05), np.full(40, 0.20)]
)
opens, highs, lows, closes = [], [], [], []

for i in range(n_days):
    open_price = price
    change = np.random.randn() * 1.8 + drift[i]
    close_price = open_price + change
    high_price = max(open_price, close_price) + abs(np.random.randn()) * 1.2
    low_price = min(open_price, close_price) - abs(np.random.randn()) * 1.2
    opens.append(open_price)
    highs.append(high_price)
    lows.append(low_price)
    closes.append(close_price)
    price = close_price

df = pd.DataFrame({"date": dates, "open": opens, "high": highs, "low": lows, "close": closes})

# Compute Ichimoku components (9, 26, 52 periods)
period_9_high = df["high"].rolling(window=9).max()
period_9_low = df["low"].rolling(window=9).min()
period_26_high = df["high"].rolling(window=26).max()
period_26_low = df["low"].rolling(window=26).min()
period_52_high = df["high"].rolling(window=52).max()
period_52_low = df["low"].rolling(window=52).min()

tenkan_sen = (period_9_high + period_9_low) / 2
kijun_sen = (period_26_high + period_26_low) / 2
senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
senkou_span_b = ((period_52_high + period_52_low) / 2).shift(26)
chikou_span = df["close"].shift(-26)

# Trim to valid data range (after 52-period lookback + 26-period shift)
start_idx = 78
df = df.iloc[start_idx:].reset_index(drop=True)
tenkan_sen = tenkan_sen.iloc[start_idx:].reset_index(drop=True)
kijun_sen = kijun_sen.iloc[start_idx:].reset_index(drop=True)
senkou_span_a = senkou_span_a.iloc[start_idx:].reset_index(drop=True)
senkou_span_b = senkou_span_b.iloc[start_idx:].reset_index(drop=True)
chikou_span = chikou_span.iloc[start_idx:].reset_index(drop=True)

# Colors
BULL_COLOR = "#26A69A"
BEAR_COLOR = "#EF5350"
TENKAN_COLOR = "#E67E22"
KIJUN_COLOR = "#8E44AD"
CHIKOU_COLOR = "#306998"
CLOUD_BULL = "rgba(38, 166, 154, 0.25)"
CLOUD_BEAR = "rgba(239, 83, 80, 0.25)"

# Plot
fig = go.Figure()

# Kumo (cloud) - fill between Senkou Span A and B
span_a_vals = senkou_span_a.values
span_b_vals = senkou_span_b.values
date_vals = df["date"].values

valid_mask = ~(np.isnan(span_a_vals) | np.isnan(span_b_vals))
valid_dates = date_vals[valid_mask]
valid_a = span_a_vals[valid_mask]
valid_b = span_b_vals[valid_mask]

# Split cloud into bullish and bearish segments for coloring
i = 0
while i < len(valid_dates):
    bullish = valid_a[i] >= valid_b[i]
    j = i + 1
    while j < len(valid_dates) and (valid_a[j] >= valid_b[j]) == bullish:
        j += 1
    if j < len(valid_dates):
        j += 1

    seg_dates = valid_dates[i:j]
    seg_a = valid_a[i:j]
    seg_b = valid_b[i:j]
    fill_color = CLOUD_BULL if bullish else CLOUD_BEAR

    fig.add_trace(
        go.Scatter(
            x=np.concatenate([seg_dates, seg_dates[::-1]]),
            y=np.concatenate([seg_a, seg_b[::-1]]),
            fill="toself",
            fillcolor=fill_color,
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    i = j - 1 if j < len(valid_dates) else j

# Senkou Span A line
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=senkou_span_a,
        mode="lines",
        line={"color": BULL_COLOR, "width": 1, "dash": "dot"},
        name="Senkou Span A",
        hovertemplate="Span A: $%{y:.2f}<extra></extra>",
    )
)

# Senkou Span B line
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=senkou_span_b,
        mode="lines",
        line={"color": BEAR_COLOR, "width": 1, "dash": "dot"},
        name="Senkou Span B",
        hovertemplate="Span B: $%{y:.2f}<extra></extra>",
    )
)

# Candlestick chart
fig.add_trace(
    go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing={"line": {"color": BULL_COLOR, "width": 1.5}, "fillcolor": BULL_COLOR},
        decreasing={"line": {"color": BEAR_COLOR, "width": 1.5}, "fillcolor": BEAR_COLOR},
        name="OHLC",
        hovertemplate=(
            "<b>%{x|%b %d, %Y}</b><br>O: $%{open:.2f} H: $%{high:.2f}<br>L: $%{low:.2f} C: $%{close:.2f}<extra></extra>"
        ),
    )
)

# Tenkan-sen (conversion line)
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=tenkan_sen,
        mode="lines",
        line={"color": TENKAN_COLOR, "width": 2},
        name="Tenkan-sen (9)",
        hovertemplate="Tenkan: $%{y:.2f}<extra></extra>",
    )
)

# Kijun-sen (base line)
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=kijun_sen,
        mode="lines",
        line={"color": KIJUN_COLOR, "width": 2},
        name="Kijun-sen (26)",
        hovertemplate="Kijun: $%{y:.2f}<extra></extra>",
    )
)

# Chikou Span (lagging line)
fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=chikou_span,
        mode="lines",
        line={"color": CHIKOU_COLOR, "width": 1.5, "dash": "dash"},
        name="Chikou Span",
        hovertemplate="Chikou: $%{y:.2f}<extra></extra>",
    )
)

# Layout
fig.update_layout(
    title={
        "text": (
            "<b>Ichimoku Cloud Overlay</b>"
            "<br><span style='color:#777;font-size:15px;font-weight:normal'>"
            "indicator-ichimoku · plotly · pyplots.ai</span>"
        ),
        "font": {"size": 28, "color": "#222", "family": "Arial"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    xaxis={
        "title": {"text": "Date", "font": {"size": 22, "color": "#444", "family": "Arial"}},
        "tickfont": {"size": 18, "color": "#555", "family": "Arial"},
        "tickformat": "%b %Y",
        "rangeslider": {"visible": False},
        "rangebreaks": [{"bounds": ["sat", "mon"]}],
        "showgrid": False,
        "linecolor": "#ccc",
        "linewidth": 1,
    },
    yaxis={
        "title": {"text": "Price (USD)", "font": {"size": 22, "color": "#444", "family": "Arial"}},
        "tickfont": {"size": 18, "color": "#555", "family": "Arial"},
        "tickprefix": "$",
        "gridcolor": "rgba(180, 180, 180, 0.2)",
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": "#ccc",
        "linewidth": 1,
    },
    legend={
        "font": {"size": 16, "family": "Arial"},
        "bgcolor": "rgba(255,255,255,0.85)",
        "bordercolor": "#ddd",
        "borderwidth": 1,
        "x": 0.01,
        "y": 0.01,
        "xanchor": "left",
        "yanchor": "bottom",
        "orientation": "h",
    },
    template="plotly_white",
    plot_bgcolor="#FAFAFA",
    paper_bgcolor="white",
    margin={"l": 90, "r": 50, "t": 110, "b": 80},
    hoverlabel={"bgcolor": "white", "font_size": 14, "bordercolor": "#ccc"},
    font={"family": "Arial"},
)

# Highlight key TK cross signal (Tenkan crosses above Kijun = bullish signal)
tk_diff = tenkan_sen - kijun_sen
for idx in range(1, len(tk_diff)):
    if pd.notna(tk_diff.iloc[idx]) and pd.notna(tk_diff.iloc[idx - 1]):
        if tk_diff.iloc[idx - 1] < 0 and tk_diff.iloc[idx] >= 0:
            cross_date = df["date"].iloc[idx]
            cross_price = tenkan_sen.iloc[idx]
            fig.add_annotation(
                x=cross_date,
                y=cross_price,
                text="<b>Bullish TK Cross</b>",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
                arrowcolor="#26A69A",
                ax=0,
                ay=-50,
                font={"size": 14, "color": "#26A69A", "family": "Arial"},
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#26A69A",
                borderwidth=1.5,
                borderpad=4,
            )
            break

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
