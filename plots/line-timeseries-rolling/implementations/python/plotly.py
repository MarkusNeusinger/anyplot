"""anyplot.ai
line-timeseries-rolling: Time Series with Rolling Average Overlay
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
WINDOW = 14  # rolling window length in observations (days for daily data)

# Columns: set these to your table's column names
DATE = "Date"  # role: date
VALUE = "Temperature (°C)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("temperature.csv")
np.random.seed(42)
n_days = 200
days = np.arange(n_days)
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=n_days, freq="D"),
        VALUE: 12 + 15 * np.sin(2 * np.pi * days / 365 - np.pi / 2) + 0.02 * days + np.random.randn(n_days) * 3,
    }
)

# Plot: reads only df and the constants above
rolling = df[VALUE].rolling(window=WINDOW).mean()  # NaN until the window is filled

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[DATE],
        y=df[VALUE],
        mode="lines",
        name="Raw Data",
        line=dict(color=IMPRINT_PALETTE[0], width=1),
        opacity=0.65,
    )
)
fig.add_trace(
    go.Scatter(
        x=df[DATE],
        y=rolling,
        mode="lines",
        name=f"{WINDOW}-Day Rolling Average",
        line=dict(color=IMPRINT_PALETTE[1], width=3),
    )
)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=80, r=40, t=80, b=60),
    title=dict(
        text="line-timeseries-rolling · python · plotly · anyplot.ai",
        font=dict(size=16, color=INK),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text=DATE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        zerolinewidth=1,
    ),
    yaxis=dict(
        title=dict(text=VALUE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        zerolinewidth=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        font=dict(size=11, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
)

# Output
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
