""" anyplot.ai
line-markers: Line Plot with Markers
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"
COLOR_2 = "#C475FD"
COLOR_3 = "#4467A3"

# Data - experimental temperature readings over time
np.random.seed(42)
x = np.arange(0, 15)

# Three sensor series with different patterns
sensor_a = 20 + np.cumsum(np.random.randn(15) * 0.8)
sensor_b = 22 + np.cumsum(np.random.randn(15) * 0.6) - 2
sensor_c = 18 + np.cumsum(np.random.randn(15) * 1.0) + 1

# Create figure
fig = go.Figure()

# Add traces with different marker styles
fig.add_trace(
    go.Scatter(
        x=x,
        y=sensor_a,
        mode="lines+markers",
        name="Sensor A",
        line=dict(color=BRAND, width=4),
        marker=dict(size=16, symbol="circle", color=BRAND, line=dict(width=2, color=PAGE_BG)),
        hovertemplate="<b>Sensor A</b><br>Time: %{x}h<br>Temperature: %{y:.1f}°C<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=x,
        y=sensor_b,
        mode="lines+markers",
        name="Sensor B",
        line=dict(color=COLOR_2, width=4),
        marker=dict(size=16, symbol="square", color=COLOR_2, line=dict(width=2, color=PAGE_BG)),
        hovertemplate="<b>Sensor B</b><br>Time: %{x}h<br>Temperature: %{y:.1f}°C<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=x,
        y=sensor_c,
        mode="lines+markers",
        name="Sensor C",
        line=dict(color=COLOR_3, width=4),
        marker=dict(size=16, symbol="diamond", color=COLOR_3, line=dict(width=2, color=PAGE_BG)),
        hovertemplate="<b>Sensor C</b><br>Time: %{x}h<br>Temperature: %{y:.1f}°C<extra></extra>",
    )
)

# Layout with theme-adaptive styling
fig.update_layout(
    title=dict(text="line-markers · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Time (hours)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        dtick=2,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Temperature (°C)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    legend=dict(
        font=dict(size=16, color=INK_SOFT),
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
    margin=dict(l=100, r=160, t=100, b=80),
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
