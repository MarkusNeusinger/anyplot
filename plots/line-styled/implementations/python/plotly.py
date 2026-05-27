""" anyplot.ai
line-styled: Styled Line Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-12
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Okabe-Ito colors (position 1 is always brand green)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Temperature readings from different environments over 24 hours
np.random.seed(42)
hours = np.arange(0, 24)

# Simulate temperature patterns for different locations
sensor_a = 15 + 8 * np.sin((hours - 6) * np.pi / 12) + np.random.normal(0, 0.5, 24)
sensor_b = 20 + 3 * np.sin((hours - 8) * np.pi / 12) + np.random.normal(0, 0.3, 24)
sensor_c = 18 + 5 * np.sin((hours - 7) * np.pi / 12) + np.random.normal(0, 0.4, 24)
sensor_d = 22 + 2 * np.sin((hours - 10) * np.pi / 12) + np.random.normal(0, 0.2, 24)

# Create figure
fig = go.Figure()

# Add traces with different line styles and Okabe-Ito colors
fig.add_trace(
    go.Scatter(
        x=hours,
        y=sensor_a,
        mode="lines",
        name="Outdoor Sensor",
        line=dict(dash="solid", width=4, color=IMPRINT[0]),
        hovertemplate="<b>Outdoor</b><br>Hour: %{x}<br>Temp: %{y:.1f}°C<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=hours,
        y=sensor_b,
        mode="lines",
        name="Indoor Sensor",
        line=dict(dash="dash", width=4, color=IMPRINT[1]),
        hovertemplate="<b>Indoor</b><br>Hour: %{x}<br>Temp: %{y:.1f}°C<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=hours,
        y=sensor_c,
        mode="lines",
        name="Greenhouse Sensor",
        line=dict(dash="dot", width=4, color=IMPRINT[2]),
        hovertemplate="<b>Greenhouse</b><br>Hour: %{x}<br>Temp: %{y:.1f}°C<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=hours,
        y=sensor_d,
        mode="lines",
        name="Storage Sensor",
        line=dict(dash="dashdot", width=4, color=IMPRINT[3]),
        hovertemplate="<b>Storage</b><br>Hour: %{x}<br>Temp: %{y:.1f}°C<extra></extra>",
    )
)

# Update layout with theme-adaptive styling
fig.update_layout(
    title=dict(text="line-styled · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Hour of Day", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        tickmode="linear",
        tick0=0,
        dtick=4,
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        range=[-0.5, 23.5],
    ),
    yaxis=dict(
        title=dict(text="Temperature (°C)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
    ),
    legend=dict(
        font=dict(size=18, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=100, r=60, t=100, b=80),
    hovermode="x unified",
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
