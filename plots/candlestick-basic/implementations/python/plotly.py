"""anyplot.ai
candlestick-basic: Basic Candlestick Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-30
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: rising = position 1, falling = position 5 (finance gain/loss semantics)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
RISING_COLOR = IMPRINT_PALETTE[0]
FALLING_COLOR = IMPRINT_PALETTE[4]

# Columns: set these to your table's column names
DATE = "Time (UTC)"  # role: date
OPEN = "Open (USD)"  # role: open
HIGH = "High (USD)"  # role: high
LOW = "Low (USD)"  # role: low
CLOSE = "Close (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("eth_usd_hourly.csv")
rng = np.random.default_rng(42)
n_periods = 60
times = pd.date_range("2025-03-10 00:00", periods=n_periods, freq="h")
closes = 3200 * np.exp(np.cumsum(rng.normal(0.0002, 0.006, n_periods)))
opens = np.concatenate([[3200.0], closes[:-1]])
spread = opens * 0.003
highs = np.maximum(opens, closes) + np.abs(rng.normal(0, 1, n_periods)) * spread
lows = np.minimum(opens, closes) - np.abs(rng.normal(0, 1, n_periods)) * spread
df = pd.DataFrame({DATE: times, OPEN: opens, HIGH: highs, LOW: lows, CLOSE: closes})

# Plot: reads only df and the constants above
title_text = "ETH/USD Hourly Price · candlestick-basic · python · plotly · anyplot.ai"
fig = go.Figure(
    go.Candlestick(
        x=df[DATE],
        open=df[OPEN],
        high=df[HIGH],
        low=df[LOW],
        close=df[CLOSE],
        increasing={"line": {"color": RISING_COLOR, "width": 1.5}, "fillcolor": RISING_COLOR},
        decreasing={"line": {"color": FALLING_COLOR, "width": 1.5}, "fillcolor": FALLING_COLOR},
        whiskerwidth=0,
        hovertemplate=(
            "<b>%{x|%b %d, %H:%M}</b><br>"
            "Open: $%{open:,.2f}<br>"
            "High: $%{high:,.2f}<br>"
            "Low: $%{low:,.2f}<br>"
            "Close: $%{close:,.2f}<extra></extra>"
        ),
    )
)

fig.update_layout(
    autosize=False,
    template="plotly_white",
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"family": "Arial", "color": INK},
    showlegend=False,
    title={"text": title_text, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": "%b %d<br>%H:%M",
        "dtick": 6 * 3600 * 1000,
        "rangeslider": {"visible": False},
        "showgrid": False,
        "showline": True,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Price (USD)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickprefix": "$",
        "tickformat": ",.0f",
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "showline": False,
    },
    margin={"l": 80, "r": 40, "t": 60, "b": 60},
    hoverlabel={"font_size": 10},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
