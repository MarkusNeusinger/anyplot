""" anyplot.ai
density-rug: Density Plot with Rug Marks
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Response times for a web application (in milliseconds)
np.random.seed(42)
# Create a bimodal distribution to show interesting KDE behavior
response_times = np.concatenate(
    [
        np.random.normal(120, 25, 80),  # Fast responses
        np.random.normal(250, 40, 40),  # Slower responses
    ]
)

# Compute KDE
kde = gaussian_kde(response_times)
x_range = np.linspace(response_times.min() - 30, response_times.max() + 30, 500)
density = kde(x_range)

# Create figure
fig = go.Figure()

# Add filled KDE curve with brand color
fig.add_trace(
    go.Scatter(
        x=x_range,
        y=density,
        mode="lines",
        fill="tozeroy",
        fillcolor=f"rgba({int(BRAND[1:3], 16)}, {int(BRAND[3:5], 16)}, {int(BRAND[5:7], 16)}, 0.35)",
        line=dict(color=BRAND, width=3),
        name="Density",
        hovertemplate="Time: %{x:.1f} ms<br>Density: %{y:.4f}<extra></extra>",
    )
)

# Add rug marks at y=0
rug_height = max(density) * 0.04
fig.add_trace(
    go.Scatter(
        x=response_times,
        y=np.zeros_like(response_times) - rug_height * 0.5,
        mode="markers",
        marker=dict(
            symbol="line-ns",
            size=14,
            line=dict(width=2, color=f"rgba({int(BRAND[1:3], 16)}, {int(BRAND[3:5], 16)}, {int(BRAND[5:7], 16)}, 0.6)"),
            color=f"rgba({int(BRAND[1:3], 16)}, {int(BRAND[3:5], 16)}, {int(BRAND[5:7], 16)}, 0.6)",
        ),
        name="Observations",
        hovertemplate="Response Time: %{x:.1f} ms<extra></extra>",
    )
)

# Layout with theme-adaptive colors
fig.update_layout(
    title=dict(
        text="density-rug · Python · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Response Time (ms)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        showline=True,
        linewidth=2,
        linecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Density", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        showline=True,
        linewidth=2,
        linecolor=INK_SOFT,
        rangemode="tozero",
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=True,
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
    margin=dict(l=100, r=60, t=100, b=100),
)

# Adjust y-axis range to include rug marks below zero
fig.update_yaxes(range=[-rug_height * 1.5, max(density) * 1.08])

# Save as PNG (4800 x 2700 px)
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
