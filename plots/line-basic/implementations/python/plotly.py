""" anyplot.ai
line-basic: Basic Line Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-07
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

# Imprint palette: first position is the single series color
BRAND = "#009E73"

# Columns: set these to your table's column names
MONTH = "Month"  # role: x
TEMPERATURE = "Temperature (°C)"  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("temperature.csv")
np.random.seed(42)
month_numbers = np.arange(1, 13)
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        TEMPERATURE: 15 + 12 * np.sin((month_numbers - 4) * np.pi / 6) + np.random.randn(12) * 1.5,
    }
)

# Plot: reads only df and the constants above
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[MONTH],
        y=df[TEMPERATURE],
        mode="lines+markers",
        line={"color": BRAND, "width": 3},
        marker={"size": 8, "color": BRAND},
        hovertemplate="%{x}<br>%{y:.1f}<extra></extra>",
    )
)

# Style
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "line-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": MONTH, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "showline": True,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": TEMPERATURE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "showline": True,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    hovermode="x",
    margin={"t": 80, "b": 60, "l": 80, "r": 40},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
