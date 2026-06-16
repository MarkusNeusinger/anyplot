""" anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-19
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette — positions 1–4
PRICE_COLOR = "#009E73"  # position 1 — first series (close price)
SMA20_COLOR = "#C475FD"  # position 2
SMA50_COLOR = "#4467A3"  # position 3
SMA200_COLOR = "#BD8233"  # position 4

# Data
np.random.seed(42)

n_days = 300
dates = pd.date_range(start="2025-01-01", periods=n_days, freq="B")

initial_price = 150.0
returns = np.random.normal(0.0005, 0.018, n_days)
price = initial_price * np.cumprod(1 + returns)
trend = np.sin(np.linspace(0, 3 * np.pi, n_days)) * 15
price = price + trend

df = pd.DataFrame({"date": dates, "close": price})
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["close"],
        mode="lines",
        name="Close Price",
        line={"color": PRICE_COLOR, "width": 3},
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["sma_20"],
        mode="lines",
        name="SMA 20",
        line={"color": SMA20_COLOR, "width": 2},
        hovertemplate="Date: %{x|%Y-%m-%d}<br>SMA 20: $%{y:.2f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["sma_50"],
        mode="lines",
        name="SMA 50",
        line={"color": SMA50_COLOR, "width": 2},
        hovertemplate="Date: %{x|%Y-%m-%d}<br>SMA 50: $%{y:.2f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["sma_200"],
        mode="lines",
        name="SMA 200",
        line={"color": SMA200_COLOR, "width": 2},
        hovertemplate="Date: %{x|%Y-%m-%d}<br>SMA 200: $%{y:.2f}<extra></extra>",
    )
)

# Style
fig.update_layout(
    title={
        "text": "indicator-sma · python · plotly · anyplot.ai", "font": {"size": 28, "color": INK}, "x": 0.5, "xanchor": "center"
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={
        "title": {"text": "Date", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Price ($)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "tickformat": "$.0f",
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    legend={
        "font": {"size": 18, "color": INK_SOFT},
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 100, "r": 60, "t": 100, "b": 80},
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
