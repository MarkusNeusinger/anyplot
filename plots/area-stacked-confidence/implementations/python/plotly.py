""" anyplot.ai
area-stacked-confidence: Stacked Area Chart with Confidence Bands
Library: plotly 6.7.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-18
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (positions 1-3 for three series)
HYDRO_COLOR = "#009E73"  # Okabe-Ito position 1 (brand green)
WIND_COLOR = "#C475FD"  # Okabe-Ito position 2 (vermillion)
SOLAR_COLOR = "#4467A3"  # Okabe-Ito position 3 (blue)

# Data - Quarterly energy consumption forecast by source with uncertainty bands
np.random.seed(42)
quarters = [d.strftime("%Y-%m-%d") for d in pd.date_range("2020-01-01", periods=20, freq="QE")]

# Base values for energy consumption (in TWh)
hydro_base = np.linspace(100, 110, 20) + np.random.randn(20) * 3
wind_base = np.linspace(80, 150, 20) + np.random.randn(20) * 8
solar_base = np.linspace(50, 120, 20) + np.random.randn(20) * 5

# Uncertainty increases over time (forecast uncertainty)
uncertainty_growth = np.linspace(1, 2.5, 20)
hydro_lower = hydro_base - 8 * uncertainty_growth
hydro_upper = hydro_base + 8 * uncertainty_growth
wind_lower = wind_base - 15 * uncertainty_growth
wind_upper = wind_base + 15 * uncertainty_growth
solar_lower = solar_base - 10 * uncertainty_growth
solar_upper = solar_base + 10 * uncertainty_growth

# Calculate stacked positions for central values
hydro_stack = hydro_base
wind_stack = hydro_base + wind_base
solar_stack = hydro_base + wind_base + solar_base

# Calculate stacked positions for confidence bands
hydro_lower_stack = hydro_lower
hydro_upper_stack = hydro_upper

wind_lower_stack = hydro_lower + wind_lower
wind_upper_stack = hydro_upper + wind_upper

solar_lower_stack = hydro_lower + wind_lower + solar_lower
solar_upper_stack = hydro_upper + wind_upper + solar_upper

# Create figure
fig = go.Figure()

# Hydro confidence band (bottom layer)
fig.add_trace(
    go.Scatter(
        x=quarters + quarters[::-1],
        y=list(hydro_upper_stack) + list(hydro_lower_stack[::-1]),
        fill="toself",
        fillcolor="rgba(0, 158, 115, 0.25)",
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False,
        name="Hydro Band",
        hoverinfo="skip",
    )
)

# Hydro central area
fig.add_trace(
    go.Scatter(
        x=quarters,
        y=hydro_stack,
        mode="lines",
        line=dict(color=HYDRO_COLOR, width=3),
        name="Hydro",
        fill="tozeroy",
        fillcolor="rgba(0, 158, 115, 0.6)",
    )
)

# Wind confidence band (middle layer)
fig.add_trace(
    go.Scatter(
        x=quarters + quarters[::-1],
        y=list(wind_upper_stack) + list(wind_lower_stack[::-1]),
        fill="toself",
        fillcolor="rgba(196, 117, 253, 0.25)",
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
        line=dict(color=WIND_COLOR, width=3),
        name="Wind",
        fill="tonexty",
        fillcolor="rgba(196, 117, 253, 0.6)",
    )
)

# Solar confidence band (top layer)
fig.add_trace(
    go.Scatter(
        x=quarters + quarters[::-1],
        y=list(solar_upper_stack) + list(solar_lower_stack[::-1]),
        fill="toself",
        fillcolor="rgba(68, 103, 163, 0.25)",
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
        line=dict(color=SOLAR_COLOR, width=3),
        name="Solar",
        fill="tonexty",
        fillcolor="rgba(68, 103, 163, 0.6)",
    )
)

# Layout
fig.update_layout(
    title=dict(
        text="area-stacked-confidence · Python · plotly · anyplot.ai",
        font=dict(size=28, color=INK),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="Quarter", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Energy Consumption (TWh)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    legend=dict(
        font=dict(size=18, color=INK_SOFT), x=0.02, y=0.98, bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    hovermode="x unified",
    margin=dict(l=80, r=40, t=80, b=60),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
