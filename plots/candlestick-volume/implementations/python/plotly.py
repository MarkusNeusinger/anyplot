""" anyplot.ai
candlestick-volume: Stock Candlestick Chart with Volume
Library: plotly 7.1.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: position 1 for up days, position 5 for down days
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_UP = IMPRINT_PALETTE[0]
COLOR_DOWN = IMPRINT_PALETTE[4]

# Column constants
DATE = "Date"  # role: date
OPEN = "Open ($)"  # role: open
HIGH = "High ($)"  # role: high
LOW = "Low ($)"  # role: low
CLOSE = "Close ($)"  # role: close
VOLUME = "Volume"  # role: volume

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv", parse_dates=["Date"])
np.random.seed(42)
n_days = 60
dates = pd.date_range("2024-01-02", periods=n_days, freq="B")  # business days

# Random-walk closes; each open is the previous close
start_price = 150.0
returns = np.random.normal(0.0005, 0.02, n_days)
close = start_price * np.cumprod(1 + returns)
open_prices = np.roll(close, 1)
open_prices[0] = start_price

# High/low extend beyond the body by part of a realistic intraday range
daily_range = np.abs(np.random.normal(0.015, 0.008, n_days)) * close
high = np.maximum(open_prices, close) + daily_range * np.random.uniform(0.3, 0.7, n_days)
low = np.minimum(open_prices, close) - daily_range * np.random.uniform(0.3, 0.7, n_days)

# Volume grows with the size of the daily move
price_change = np.abs(close - open_prices) / open_prices
volume = (5_000_000 * (1 + 3 * price_change) * np.random.uniform(0.7, 1.3, n_days)).astype(int)

df = pd.DataFrame({DATE: dates, OPEN: open_prices, HIGH: high, LOW: low, CLOSE: close, VOLUME: volume})

# Plot
is_up = df[CLOSE] >= df[OPEN]
bar_colors = np.where(is_up, COLOR_UP, COLOR_DOWN)

# Price pane ~75% of the height, volume pane ~25%, one shared x-axis
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])

fig.add_trace(
    go.Candlestick(
        x=df[DATE],
        open=df[OPEN],
        high=df[HIGH],
        low=df[LOW],
        close=df[CLOSE],
        increasing={"line": {"color": COLOR_UP, "width": 1}, "fillcolor": COLOR_UP},
        decreasing={"line": {"color": COLOR_DOWN, "width": 1}, "fillcolor": COLOR_DOWN},
        name="Price",
        showlegend=False,
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Bar(x=df[DATE], y=df[VOLUME], marker={"color": bar_colors, "line": {"width": 0}}, name=VOLUME, showlegend=False),
    row=2,
    col=1,
)

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={
        "text": "candlestick-volume · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    hovermode="x unified",
    xaxis_rangeslider_visible=False,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

# One vertical crosshair guide running through both panes
fig.update_xaxes(
    showspikes=True,
    spikemode="across",
    spikesnap="cursor",
    spikecolor=INK_SOFT,
    spikethickness=1,
    spikedash="solid",
    tickfont={"size": 10, "color": INK_SOFT},
    gridcolor=GRID,
    gridwidth=1,
    linecolor=INK_SOFT,
    zerolinecolor=INK_SOFT,
)
fig.update_xaxes(title={"text": DATE, "font": {"size": 12, "color": INK}}, row=2, col=1)

fig.update_yaxes(
    tickfont={"size": 10, "color": INK_SOFT}, gridcolor=GRID, gridwidth=1, linecolor=INK_SOFT, zerolinecolor=INK_SOFT
)
fig.update_yaxes(title={"text": "Price ($)", "font": {"size": 12, "color": INK}}, tickformat="$.0f", row=1, col=1)
fig.update_yaxes(title={"text": VOLUME, "font": {"size": 12, "color": INK}}, tickformat=".2s", row=2, col=1)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
