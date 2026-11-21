""" anyplot.ai
line-markers: Line Plot with Markers
Library: plotly 7.1.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
Y_LABEL = "Temperature (°C)"
MARKER_SYMBOLS = ["circle", "square", "diamond", "triangle-up", "cross", "x", "star", "hexagon"]  # one shape per series

# Columns: set these to your table's column names
TIME = "Time (hours)"  # role: x
SENSORS = ["Sensor A", "Sensor B", "Sensor C"]  # role: y

# Data: replace this block with your own table, for example df = pd.read_csv("readings.csv")
np.random.seed(42)
df = pd.DataFrame(
    {
        TIME: np.arange(0, 15),
        SENSORS[0]: 20 + np.cumsum(np.random.randn(15) * 0.8),
        SENSORS[1]: 22 + np.cumsum(np.random.randn(15) * 0.6) - 2,
        SENSORS[2]: 18 + np.cumsum(np.random.randn(15) * 1.0) + 1,
    }
)

# Plot
fig = go.Figure()
for i, sensor in enumerate(SENSORS):
    color = IMPRINT_PALETTE[i]
    fig.add_trace(
        go.Scatter(
            x=df[TIME],
            y=df[sensor],
            mode="lines+markers",
            name=sensor,
            line=dict(color=color, width=2.5),
            marker=dict(size=10, symbol=MARKER_SYMBOLS[i], color=color, line=dict(width=1, color=PAGE_BG)),
            hovertemplate=f"<b>{sensor}</b><br>{TIME}: %{{x}}<br>Temperature: %{{y:.1f}}°C<extra></extra>",
        )
    )

fig.update_layout(
    autosize=False,
    title=dict(
        text="line-markers · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text=TIME, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        dtick=2,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text=Y_LABEL, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    legend=dict(
        font=dict(size=10, color=INK_SOFT),
        x=1.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=70, r=100, t=60, b=60),
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
