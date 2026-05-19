""" anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-19
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

# Okabe-Ito palette — positions 1-5 in canonical order
BRAND = "#009E73"  # price line (first series)
EMA_SHORT = "#D55E00"  # EMA 12
EMA_LONG = "#0072B2"  # EMA 26
GOLDEN_CLR = "#CC79A7"  # golden cross marker
DEATH_CLR = "#E69F00"  # death cross marker

# Data — realistic stock price with trend, consolidation, and recovery
np.random.seed(42)
n_days = 120

dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

base_price = 150
returns = np.random.normal(0.001, 0.015, n_days)
trend = np.concatenate([np.linspace(0, 0.15, 40), np.linspace(0.15, 0.12, 30), np.linspace(0.12, 0.25, 50)])
close_prices = base_price * np.exp(np.cumsum(returns) + trend)

df = pd.DataFrame({"date": dates, "close": close_prices})
df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

crossover_up = (df["ema_12"] > df["ema_26"]) & (df["ema_12"].shift(1) <= df["ema_26"].shift(1))
crossover_down = (df["ema_12"] < df["ema_26"]) & (df["ema_12"].shift(1) >= df["ema_26"].shift(1))

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["close"],
        mode="lines",
        name="Price",
        line={"color": BRAND, "width": 3},
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["ema_12"],
        mode="lines",
        name="EMA 12",
        line={"color": EMA_SHORT, "width": 2},
        hovertemplate="Date: %{x|%Y-%m-%d}<br>EMA 12: $%{y:.2f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["ema_26"],
        mode="lines",
        name="EMA 26",
        line={"color": EMA_LONG, "width": 2},
        hovertemplate="Date: %{x|%Y-%m-%d}<br>EMA 26: $%{y:.2f}<extra></extra>",
    )
)

golden_cross = df[crossover_up]
if len(golden_cross) > 0:
    fig.add_trace(
        go.Scatter(
            x=golden_cross["date"],
            y=golden_cross["ema_12"],
            mode="markers",
            name="Golden Cross ▲",
            marker={"color": GOLDEN_CLR, "size": 16, "symbol": "triangle-up", "line": {"color": PAGE_BG, "width": 2}},
            hovertemplate="Golden Cross<br>Date: %{x|%Y-%m-%d}<br>EMA: $%{y:.2f}<extra></extra>",
        )
    )

death_cross = df[crossover_down]
if len(death_cross) > 0:
    fig.add_trace(
        go.Scatter(
            x=death_cross["date"],
            y=death_cross["ema_12"],
            mode="markers",
            name="Death Cross ▼",
            marker={"color": DEATH_CLR, "size": 16, "symbol": "triangle-down", "line": {"color": PAGE_BG, "width": 2}},
            hovertemplate="Death Cross<br>Date: %{x|%Y-%m-%d}<br>EMA: $%{y:.2f}<extra></extra>",
        )
    )

# Style — theme-adaptive chrome throughout
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "indicator-ema · python · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Date", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "showgrid": True,
        "rangeslider": {"visible": True, "bgcolor": PAGE_BG, "bordercolor": INK_SOFT, "thickness": 0.08},
    },
    yaxis={
        "title": {"text": "Price (USD)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickformat": "$,.0f",
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "showgrid": True,
    },
    legend={
        "font": {"size": 18, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    hovermode="x unified",
    margin={"l": 80, "r": 40, "t": 80, "b": 80},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
