"""anyplot.ai
ohlc-bar: OHLC Bar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: position 1 for up bars, position 5 (red) for down bars
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
UP_COLOR = IMPRINT_PALETTE[0]
DOWN_COLOR = IMPRINT_PALETTE[4]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
OPEN = "Open (USD)"  # role: open
HIGH = "High (USD)"  # role: high
LOW = "Low (USD)"  # role: low
CLOSE = "Close (USD)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
rng = np.random.default_rng(42)
n_days = 45
start_price = 150.0
dates = pd.date_range(start="2024-06-03", periods=n_days, freq="B")
close_prices = start_price * np.cumprod(1 + rng.normal(0.001, 0.02, n_days))
open_prices = np.concatenate([[start_price], close_prices[:-1]])
intraday_range = close_prices * rng.uniform(0.01, 0.03, n_days)
df = pd.DataFrame(
    {
        DATE: dates,
        OPEN: open_prices,
        HIGH: np.maximum(open_prices, close_prices) + rng.uniform(0, 1, n_days) * intraday_range,
        LOW: np.minimum(open_prices, close_prices) - rng.uniform(0, 1, n_days) * intraday_range,
        CLOSE: close_prices,
    }
)

# Plot: reads only df and the constants above
fig = go.Figure(
    go.Ohlc(
        x=df[DATE],
        open=df[OPEN],
        high=df[HIGH],
        low=df[LOW],
        close=df[CLOSE],
        increasing={"line": {"color": UP_COLOR, "width": 2.5}},
        decreasing={"line": {"color": DOWN_COLOR, "width": 2.5}},
        tickwidth=0.45,
        name="Price",
    )
)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 80, "r": 40, "t": 70, "b": 60},
    title={"text": "ohlc-bar · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}},
    xaxis={
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "rangeslider": {"visible": False},
        "tickformat": "%b %d",
    },
    yaxis={
        "title": {"text": "Price (USD)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickprefix": "$",
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
