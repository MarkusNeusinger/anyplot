"""anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-19
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close
SMA_SHORT = "SMA 20"  # role: sma_short
SMA_MEDIUM = "SMA 50"  # role: sma_medium
SMA_LONG = "SMA 200"  # role: sma_long

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 300
returns = np.random.normal(0.0005, 0.018, n_days)
price = 150.0 * np.cumprod(1 + returns) + np.sin(np.linspace(0, 3 * np.pi, n_days)) * 15

df = pd.DataFrame({DATE: pd.date_range(start="2025-01-01", periods=n_days, freq="B"), CLOSE: price})
df[SMA_SHORT] = df[CLOSE].rolling(window=20).mean()
df[SMA_MEDIUM] = df[CLOSE].rolling(window=50).mean()
df[SMA_LONG] = df[CLOSE].rolling(window=200).mean()

# Plot: reads only df and the constants above
fig = go.Figure()
series = [CLOSE, SMA_SHORT, SMA_MEDIUM, SMA_LONG]
for i, col in enumerate(series):
    fig.add_trace(
        go.Scatter(
            x=df[DATE],
            y=df[col],
            mode="lines",
            name=col,
            line={"color": IMPRINT_PALETTE[i], "width": 2.5 if i == 0 else 1.75},
            hovertemplate=f"Date: %{{x|%Y-%m-%d}}<br>{col}: $%{{y:.2f}}<extra></extra>",
        )
    )

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "indicator-sma · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Price ($)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "tickformat": "$.0f",
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.98,
        "y": 0.04,
        "xanchor": "right",
        "yanchor": "bottom",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 40, "t": 60, "b": 60},
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
