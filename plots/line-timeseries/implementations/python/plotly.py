""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-20
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
BRAND = "#009E73"  # Imprint palette position 1

# Columns
DATE = "Date"  # role: date
PRICE = "Stock Price ($)"  # role: value

# Data - daily stock prices with uptrend
rng = np.random.default_rng(42)
dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
days = np.arange(len(dates))
prices = 100 + 0.15 * days + 5 * np.sin(2 * np.pi * days / 60) + rng.normal(0, 2, len(dates))
df = pd.DataFrame({DATE: dates, PRICE: prices})

# Plot
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[DATE],
        y=df[PRICE],
        mode="lines",
        line={"color": BRAND, "width": 2.5},
        hovertemplate="Date: %{x|%b %d, %Y}<br>Price: $%{y:.2f}<extra></extra>",
    )
)

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={
        "text": "line-timeseries · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": "%b %Y",
        "dtick": "M1",
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "rangeslider": {"visible": True, "thickness": 0.06},
    },
    yaxis={
        "title": {"text": PRICE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 70, "r": 40, "t": 60, "b": 50},
    showlegend=False,
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
