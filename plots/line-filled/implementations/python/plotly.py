"""anyplot.ai
line-filled: Filled Line Plot
Library: plotly | Python 3.13
Quality: pending | Created: 2026-05-12
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Monthly website traffic over a year
np.random.seed(42)
months = np.arange(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Generate realistic website traffic pattern with more variability
base_traffic = 50
seasonal = 15 * np.sin(2 * np.pi * (months - 3) / 12)
trend = 2 * months
noise = np.random.normal(0, 8, len(months))  # Increased noise for more variability
traffic = base_traffic + seasonal + trend + noise
traffic = np.maximum(traffic, 10)

# Create figure with filled area
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=month_labels,
        y=traffic,
        mode="lines",
        name="Website Traffic",
        line=dict(color=BRAND, width=4),
        fill="tozeroy",
        fillcolor="rgba(0, 158, 115, 0.35)",
        hovertemplate="%{x}: %{y:.1f}K visitors<extra></extra>",
    )
)

# Update layout with theme-adaptive colors
fig.update_layout(
    title=dict(text="line-filled · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Month", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Website Visitors (thousands)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        rangemode="tozero",
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=False,
    margin=dict(l=100, r=60, t=100, b=80),
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
