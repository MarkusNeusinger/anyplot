""" anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per panel in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SEASON_LENGTH = 12  # observations per seasonal cycle (monthly data, yearly pattern)
COMPONENTS = ["Original", "Trend", "Seasonal", "Residual"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
PASSENGERS = "Passengers (thousands)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("passengers.csv", parse_dates=["Date"])
np.random.seed(42)
n_months = 120
df = pd.DataFrame(
    {
        DATE: pd.date_range(start="2014-01-01", periods=n_months, freq="MS"),
        PASSENGERS: (
            np.linspace(100, 250, n_months)
            + 30 * np.sin(2 * np.pi * np.arange(n_months) / 12)
            + np.random.normal(0, 10, n_months)
        ),
    }
)

# Plot: reads only df and the constants above
ts = df.set_index(DATE)[PASSENGERS].interpolate(limit_direction="both")  # the decomposition needs a complete series
period = min(SEASON_LENGTH, len(ts) // 2)  # at least two full cycles
decomposition = seasonal_decompose(ts, model="additive", period=period)
series = [df[PASSENGERS].to_numpy(), decomposition.trend, decomposition.seasonal, decomposition.resid]

fig = make_subplots(rows=len(COMPONENTS), cols=1, shared_xaxes=True, vertical_spacing=0.09, subplot_titles=COMPONENTS)
for row, (name, values) in enumerate(zip(COMPONENTS, series, strict=True), start=1):
    fig.add_trace(
        go.Scatter(
            x=df[DATE],
            y=values,
            mode="lines",
            line={"color": IMPRINT_PALETTE[row - 1], "width": 2.5},
            name=name,
            hovertemplate=f"<b>{name}</b><br>%{{x|%Y-%m}}<br>%{{y:.1f}}<extra></extra>",
        ),
        row=row,
        col=1,
    )

# Style
title = "timeseries-decomposition · python · plotly · anyplot.ai"
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin={"l": 70, "r": 30, "t": 60, "b": 50},
    title={"text": title, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
)
fig.update_yaxes(
    tickfont={"size": 10, "color": INK_SOFT},
    title_font={"size": 12, "color": INK},
    title_standoff=4,
    gridcolor=GRID,
    gridwidth=1,
    linecolor=INK_SOFT,
    zeroline=False,
    nticks=4,
)
fig.update_xaxes(tickfont={"size": 10, "color": INK_SOFT}, gridcolor=GRID, gridwidth=1, linecolor=INK_SOFT)
for row in range(1, len(COMPONENTS) + 1):
    fig.update_yaxes(title_text=PASSENGERS.split(" (")[0] if row == 1 else COMPONENTS[row - 1], row=row, col=1)
fig.update_xaxes(title={"text": DATE, "font": {"size": 12, "color": INK}, "standoff": 4}, row=len(COMPONENTS), col=1)
for annotation in fig.layout.annotations:
    annotation.update(font={"size": 12, "color": INK}, x=0.0, xanchor="left", yshift=-2)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
