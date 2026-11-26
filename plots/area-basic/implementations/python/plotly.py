"""anyplot.ai
area-basic: Basic Area Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-28
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

# Imprint palette: single series, first position
BRAND = "#009E73"

# Columns: set these to your table's column names
DATE = "Date (Q1 2024)"  # role: x
VISITORS = "Visitors (daily count)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("visitors.csv")
np.random.seed(42)
n_days = 90
trend = np.linspace(0, 2500, n_days)
weekly = 1200 * np.sin(np.arange(n_days) * 2 * np.pi / 7)
noise = np.random.randn(n_days) * 400
df = pd.DataFrame(
    {
        DATE: pd.date_range("2024-01-01", periods=n_days, freq="D"),
        VISITORS: np.maximum(5000 + trend + weekly + noise, 1500).astype(int),
    }
)

# Plot
title = "Daily Website Visitors · area-basic · python · plotly · anyplot.ai"
title_fontsize = round(16 * (67 / len(title))) if len(title) > 67 else 16

# Semi-transparent gradient fill, strongest at the line, fading toward the baseline
fill_top = "rgba(0,158,115,0.45)" if THEME == "light" else "rgba(0,158,115,0.40)"
fill_bot = "rgba(0,158,115,0.12)"

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[DATE],
        y=df[VISITORS],
        mode="lines",
        fill="tozeroy",
        fillcolor=fill_top,
        fillgradient={"type": "vertical", "colorscale": [[0.0, fill_bot], [1.0, fill_top]]},
        line={"color": BRAND, "width": 3},
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>" + VISITORS + ": %{y:,}<extra></extra>",
    )
)

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={"text": title, "font": {"size": title_fontsize, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "dtick": "M1",
        "tickformat": "%b %Y",
    },
    yaxis={
        "title": {"text": VISITORS, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "tickformat": ",",
        "range": [0, df[VISITORS].max() * 1.1],
    },
    showlegend=False,
    margin={"l": 80, "r": 40, "t": 60, "b": 60},
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)

fig.update_layout(xaxis_rangeslider_visible=True)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
