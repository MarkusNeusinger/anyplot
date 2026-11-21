""" anyplot.ai
line-filled: Filled Line Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: first series is always brand green
BRAND = "#009E73"

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
TRAFFIC = "Website Visitors (thousands)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
np.random.seed(42)
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
month_index = np.arange(1, 13)
seasonal = 15 * np.sin(2 * np.pi * (month_index - 3) / 12)
noise = np.random.normal(0, 8, len(month_index))
df = pd.DataFrame({MONTH: month_names, TRAFFIC: np.maximum(50 + seasonal + 2 * month_index + noise, 10)})

# Plot: reads only df and the constants above
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[MONTH],
        y=df[TRAFFIC],
        mode="lines",
        line={"color": BRAND, "width": 3},
        fill="tozeroy",
        fillcolor="rgba(0, 158, 115, 0.35)",
        hovertemplate="%{x}: %{y:.1f}K visitors<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "line-filled · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": MONTH, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": TRAFFIC, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "rangemode": "tozero",
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
