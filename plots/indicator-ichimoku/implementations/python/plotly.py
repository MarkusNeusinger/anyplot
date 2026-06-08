"""anyplot.ai
indicator-ichimoku: Ichimoku Cloud Technical Indicator Chart
Library: plotly | Python 3.13
Quality: 90/100 | Created: 2026-03-12
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — semantic bull/bear anchor, Imprint positions 2–4 for indicator lines
BULL_COLOR = "#009E73"  # Imprint brand green — bullish/gain (semantic exception)
BEAR_COLOR = "#AE3030"  # Imprint matte red  — bearish/loss (semantic exception)
TENKAN_COLOR = "#C475FD"  # Imprint lavender (pos 2)
KIJUN_COLOR = "#4467A3"  # Imprint blue     (pos 3)
CHIKOU_COLOR = "#BD8233"  # Imprint ochre    (pos 4)
CLOUD_BULL = "rgba(0,158,115,0.20)"  # BULL at 20% opacity
CLOUD_BEAR = "rgba(174,48,48,0.20)"  # BEAR at 20% opacity

# Data — 200 trading days of simulated stock prices
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

# Convert dates to strings — kaleido cannot JSON-serialize pandas Timestamps
df["date"] = df["date"].dt.strftime("%Y-%m-%d")

# Plot
fig = go.Figure()

# Kumo (cloud) — fill between Senkou Span A and B, colored by trend direction
span_a_vals = senkou_span_a.values
span_b_vals = senkou_span_b.values
date_vals = df["date"].values

valid_mask = ~(np.isnan(span_a_vals) | np.isnan(span_b_vals))
valid_dates = date_vals[valid_mask]
valid_a = span_a_vals[valid_mask]
valid_b = span_b_vals[valid_mask]

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
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([seg_dates, seg_dates[::-1]]),
            y=np.concatenate([seg_a, seg_b[::-1]]),
            fill="toself",
            fillcolor=CLOUD_BULL if bullish else CLOUD_BEAR,
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
        line={"color": BULL_COLOR, "width": 1.5, "dash": "dot"},
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
        line={"color": BEAR_COLOR, "width": 1.5, "dash": "dot"},
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

# Chikou Span (lagging line, shifted 26 periods into the past)
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

# Title — scale font size for total length
title_text = "Ichimoku Cloud Overlay · indicator-ichimoku · python · plotly · anyplot.ai"
title_fontsize = max(11, round(16 * 67 / len(title_text)))

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={"text": title_text, "font": {"size": title_fontsize, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Date", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": "%b %Y",
        "rangeslider": {"visible": False},
        "rangebreaks": [{"bounds": ["sat", "mon"]}],
        "showgrid": False,
        "linecolor": INK_SOFT,
        "linewidth": 1,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Price (USD)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickprefix": "$",
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": INK_SOFT,
        "linewidth": 1,
    },
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 0.01,
        "y": 0.01,
        "xanchor": "left",
        "yanchor": "bottom",
        "orientation": "h",
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    hoverlabel={"bgcolor": ELEVATED_BG, "font_size": 10, "bordercolor": INK_SOFT},
)

# Annotate the first bullish TK Cross (Tenkan crosses above Kijun)
tk_diff = tenkan_sen - kijun_sen
for idx in range(1, len(tk_diff)):
    if pd.notna(tk_diff.iloc[idx]) and pd.notna(tk_diff.iloc[idx - 1]):
        if tk_diff.iloc[idx - 1] < 0 and tk_diff.iloc[idx] >= 0:
            fig.add_annotation(
                x=df["date"].iloc[idx],
                y=tenkan_sen.iloc[idx],
                text="<b>Bullish TK Cross</b>",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
                arrowcolor=BULL_COLOR,
                ax=0,
                ay=-50,
                font={"size": 10, "color": BULL_COLOR},
                bgcolor=ELEVATED_BG,
                bordercolor=BULL_COLOR,
                borderwidth=1.5,
                borderpad=4,
            )
            break

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
