""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-09
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Stock prices with uptrend
np.random.seed(42)
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
days = np.arange(len(dates))
trend = 100 + 0.15 * days
volatility = 5 * np.sin(2 * np.pi * days / 60)
noise = np.random.randn(len(dates)) * 2
prices = trend + volatility + noise

df = pd.DataFrame({"date": dates, "price": prices})

# Create plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["price"],
        mode="lines",
        line={"color": BRAND, "width": 3},
        name="Stock Price",
        hovertemplate="Date: %{x|%b %d, %Y}<br>Price: $%{y:.2f}<extra></extra>",
    )
)

# Layout for 4800x2700 px
fig.update_layout(
    title={
        "text": "line-timeseries · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Date", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickformat": "%b %Y",
        "dtick": "M1",
        "gridcolor": GRID,
        "gridwidth": 1,
        "showgrid": True,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "rangeslider": {"visible": True, "thickness": 0.05},
    },
    yaxis={
        "title": {"text": "Stock Price ($)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "showgrid": True,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 100, "r": 80, "t": 120, "b": 100},
    showlegend=False,
    hovermode="x unified",
)

# Save as PNG (4800x2700 px) and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
