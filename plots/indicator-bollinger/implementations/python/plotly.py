""" anyplot.ai
indicator-bollinger: Bollinger Bands Indicator Chart
Library: plotly 7.1.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: close price takes position 1, the bands position 2, the SMA position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW = 20  # SMA period in trading days
NUM_STD = 2  # band width in standard deviations

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Close price ($)"  # role: close
SMA = "20-day SMA"  # role: sma
UPPER = "Upper band (+2σ)"  # role: upper_band
LOWER = "Lower band (−2σ)"  # role: lower_band

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_periods = 120
dates = pd.date_range("2024-01-01", periods=n_periods, freq="B")
returns = np.random.normal(0.0005, 0.018, n_periods) + np.sin(np.linspace(0, 3 * np.pi, n_periods)) * 0.003
close = pd.Series(100 * np.cumprod(1 + returns))
sma = close.rolling(window=WINDOW).mean()
std = close.rolling(window=WINDOW).std()
df = pd.DataFrame({DATE: dates, CLOSE: close, SMA: sma, UPPER: sma + NUM_STD * std, LOWER: sma - NUM_STD * std})
df = df.dropna().reset_index(drop=True)

# Plot: reads only df and the constants above
band_r, band_g, band_b = (int(IMPRINT_PALETTE[1][i : i + 2], 16) for i in (1, 3, 5))
band_fill = f"rgba({band_r}, {band_g}, {band_b}, 0.18)"

fig = go.Figure()

# Envelope: invisible upper edge, then the lower edge filled up to it
fig.add_trace(go.Scatter(x=df[DATE], y=df[UPPER], mode="lines", line={"width": 0}, showlegend=False, hoverinfo="skip"))
fig.add_trace(
    go.Scatter(
        x=df[DATE],
        y=df[LOWER],
        mode="lines",
        line={"width": 0},
        fill="tonexty",
        fillcolor=band_fill,
        name=f"Bollinger band (±{NUM_STD}σ)",
        hoverinfo="skip",
    )
)

# Upper and lower band lines share one color
for column in (UPPER, LOWER):
    fig.add_trace(
        go.Scatter(
            x=df[DATE],
            y=df[column],
            mode="lines",
            line={"color": IMPRINT_PALETTE[1], "width": 1.5},
            name=column,
            hovertemplate=column + ": $%{y:.2f}<extra></extra>",
        )
    )

# Middle band: dashed so it reads apart from the price
fig.add_trace(
    go.Scatter(
        x=df[DATE],
        y=df[SMA],
        mode="lines",
        line={"color": IMPRINT_PALETTE[2], "width": 2, "dash": "dash"},
        name=SMA,
        hovertemplate=SMA + ": $%{y:.2f}<extra></extra>",
    )
)

# Price on top, in the brand color
fig.add_trace(
    go.Scatter(
        x=df[DATE],
        y=df[CLOSE],
        mode="lines",
        line={"color": IMPRINT_PALETTE[0], "width": 2.5},
        name=CLOSE,
        hovertemplate=CLOSE + ": $%{y:.2f}<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title={
        "text": "indicator-bollinger · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": CLOSE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": "$.0f",
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 70, "r": 30, "t": 90, "b": 55},
    hovermode="x unified",
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
