""" pyplots.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: plotly 6.5.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Quarterly energy consumption forecast by source with uncertainty bands
np.random.seed(42)
quarters = pd.date_range("2020-01-01", periods=20, freq="QE")

# Base values for energy consumption (in TWh)
solar_base = np.linspace(50, 120, 20) + np.random.randn(20) * 5
wind_base = np.linspace(80, 150, 20) + np.random.randn(20) * 8
hydro_base = np.linspace(100, 110, 20) + np.random.randn(20) * 3

# Uncertainty increases over time (forecast uncertainty)
uncertainty_growth = np.linspace(1, 2.5, 20)
solar_lower = solar_base - 10 * uncertainty_growth
solar_upper = solar_base + 10 * uncertainty_growth
wind_lower = wind_base - 15 * uncertainty_growth
wind_upper = wind_base + 15 * uncertainty_growth
hydro_lower = hydro_base - 8 * uncertainty_growth
hydro_upper = hydro_base + 8 * uncertainty_growth

# Calculate stacked positions for central values
hydro_stack = hydro_base
wind_stack = hydro_base + wind_base
solar_stack = hydro_base + wind_base + solar_base

# Calculate stacked positions for confidence bands
hydro_lower_stack = hydro_lower
hydro_upper_stack = hydro_upper

wind_lower_stack = hydro_base + wind_lower
wind_upper_stack = hydro_base + wind_upper

solar_lower_stack = hydro_base + wind_base + solar_lower
solar_upper_stack = hydro_base + wind_base + solar_upper

# Colors
hydro_color = "#306998"  # Python Blue
wind_color = "#FFD43B"  # Python Yellow
solar_color = "#E74C3C"  # Red for solar

# Create figure
fig = go.Figure()

# Hydro confidence band (bottom layer)
fig.add_trace(
    go.Scatter(
        x=list(quarters) + list(quarters[::-1]),
        y=list(hydro_upper_stack) + list(hydro_lower_stack[::-1]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.25)",
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False,
        name="Hydro Band",
        hoverinfo="skip",
    )
)

# Hydro central line
fig.add_trace(
    go.Scatter(
        x=quarters,
        y=hydro_stack,
        mode="lines",
        line=dict(color=hydro_color, width=3),
        name="Hydro",
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.6)",
    )
)

# Wind confidence band (middle layer)
fig.add_trace(
    go.Scatter(
        x=list(quarters) + list(quarters[::-1]),
        y=list(wind_upper_stack) + list(wind_lower_stack[::-1]),
        fill="toself",
        fillcolor="rgba(255, 212, 59, 0.25)",
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False,
        name="Wind Band",
        hoverinfo="skip",
    )
)

# Wind central area
fig.add_trace(
    go.Scatter(
        x=quarters,
        y=wind_stack,
        mode="lines",
        line=dict(color=wind_color, width=3),
        name="Wind",
        fill="tonexty",
        fillcolor="rgba(255, 212, 59, 0.6)",
    )
)

# Solar confidence band (top layer)
fig.add_trace(
    go.Scatter(
        x=list(quarters) + list(quarters[::-1]),
        y=list(solar_upper_stack) + list(solar_lower_stack[::-1]),
        fill="toself",
        fillcolor="rgba(231, 76, 60, 0.25)",
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False,
        name="Solar Band",
        hoverinfo="skip",
    )
)

# Solar central area
fig.add_trace(
    go.Scatter(
        x=quarters,
        y=solar_stack,
        mode="lines",
        line=dict(color=solar_color, width=3),
        name="Solar",
        fill="tonexty",
        fillcolor="rgba(231, 76, 60, 0.6)",
    )
)

# Add a dummy trace for confidence band legend
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="lines",
        line=dict(color="rgba(128, 128, 128, 0.5)", width=10),
        name="90% Confidence Band",
        showlegend=True,
    )
)

# Layout
fig.update_layout(
    title=dict(text="area-stacked-confidence · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Quarter", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.2)",
    ),
    yaxis=dict(
        title=dict(text="Energy Consumption (TWh)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(128, 128, 128, 0.2)",
    ),
    legend=dict(
        font=dict(size=18),
        x=0.02,
        y=0.98,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(128, 128, 128, 0.3)",
        borderwidth=1,
    ),
    template="plotly_white",
    hovermode="x unified",
    margin=dict(l=80, r=40, t=80, b=60),
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
