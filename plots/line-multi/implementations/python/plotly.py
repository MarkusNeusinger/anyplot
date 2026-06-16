""" anyplot.ai
line-multi: Multi-Line Comparison Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-06
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (positions 1-4 for 4 series)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Monthly sales (units) for 4 product lines over 12 months
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Product sales with distinct trends
electronics = 150 + np.cumsum(np.random.randn(12) * 10) + np.linspace(0, 50, 12)
clothing = 200 + np.cumsum(np.random.randn(12) * 8) + 20 * np.sin(np.linspace(0, 2 * np.pi, 12))
home_garden = 100 + np.cumsum(np.random.randn(12) * 6) + np.linspace(0, 30, 12)
sports = 120 + np.cumsum(np.random.randn(12) * 12)

# Plot
fig = go.Figure()

# Add traces for each product line
fig.add_trace(
    go.Scatter(
        x=months,
        y=electronics,
        name="Electronics",
        mode="lines+markers",
        line=dict(color=IMPRINT[0], width=4),
        marker=dict(size=12, symbol="circle"),
    )
)

fig.add_trace(
    go.Scatter(
        x=months,
        y=clothing,
        name="Clothing",
        mode="lines+markers",
        line=dict(color=IMPRINT[1], width=4),
        marker=dict(size=12, symbol="square"),
    )
)

fig.add_trace(
    go.Scatter(
        x=months,
        y=home_garden,
        name="Home & Garden",
        mode="lines+markers",
        line=dict(color=IMPRINT[2], width=4, dash="dash"),
        marker=dict(size=12, symbol="diamond"),
    )
)

fig.add_trace(
    go.Scatter(
        x=months,
        y=sports,
        name="Sports",
        mode="lines+markers",
        line=dict(color=IMPRINT[3], width=4, dash="dot"),
        marker=dict(size=12, symbol="triangle-up"),
    )
)

# Style
fig.update_layout(
    title=dict(text="line-multi · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Month", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Sales (Units)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridwidth=1,
        gridcolor=GRID,
        linecolor=INK_SOFT,
    ),
    legend=dict(
        font=dict(size=16, color=INK_SOFT),
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
    margin=dict(l=100, r=80, t=120, b=100),
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
