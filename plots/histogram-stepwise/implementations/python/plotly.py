""" anyplot.ai
histogram-stepwise: Step Histogram
Library: plotly 6.7.0 | Python 3.13.13
Quality: 80/100 | Created: 2026-05-12
"""

import os

import numpy as np
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"

# Data
np.random.seed(42)
values = np.random.normal(loc=100, scale=18, size=1200)

# Create histogram
counts, bins = np.histogram(values, bins=32)

# Create step line coordinates
x_coords = []
y_coords = []

for i in range(len(counts)):
    x_coords.append(bins[i])
    y_coords.append(0)
    x_coords.append(bins[i])
    y_coords.append(counts[i])
    x_coords.append(bins[i + 1])
    y_coords.append(counts[i])
    x_coords.append(bins[i + 1])
    y_coords.append(0)

# Plot
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=x_coords,
        y=y_coords,
        mode="lines",
        line={"color": BRAND, "width": 3},
        hovertemplate="Value: %{x:.1f}<br>Frequency: %{y}<extra></extra>",
    )
)

fig.update_layout(
    title={"text": "histogram-stepwise · plotly · anyplot.ai", "font": {"size": 28, "color": INK}},
    xaxis={
        "title": {"text": "Value", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Frequency", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    hovermode="closest",
    margin={"l": 80, "r": 60, "t": 100, "b": 80},
    showlegend=False,
)

fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
