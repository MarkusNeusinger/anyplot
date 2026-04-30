""" anyplot.ai
stem-basic: Basic Stem Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-04-30
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.20)" if THEME == "light" else "rgba(240,239,232,0.20)"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Discrete signal samples (damped oscillation)
np.random.seed(42)
x = np.arange(0, 30)
y = np.exp(-x / 10) * np.cos(x * 0.8) + np.random.randn(30) * 0.05

# Plot
fig = go.Figure()

# Baseline at y=0
fig.add_trace(
    go.Scatter(
        x=[x.min() - 0.5, x.max() + 0.5],
        y=[0, 0],
        mode="lines",
        line={"color": INK_SOFT, "width": 2},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Stems (vertical lines from baseline to data points)
for xi, yi in zip(x, y, strict=True):
    fig.add_trace(
        go.Scatter(
            x=[xi, xi], y=[0, yi], mode="lines", line={"color": BRAND, "width": 2}, showlegend=False, hoverinfo="skip"
        )
    )

# Markers at the top of each stem
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        mode="markers",
        marker={"color": BRAND, "size": 16, "line": {"color": PAGE_BG, "width": 2}},
        showlegend=False,
        hovertemplate="Sample: %{x}<br>Amplitude: %{y:.3f}<extra></extra>",
    )
)

# Style
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "stem-basic · plotly · anyplot.ai",
        "font": {"size": 42, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Sample Index (n)", "font": {"size": 36, "color": INK}},
        "tickfont": {"size": 28, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Amplitude (a.u.)", "font": {"size": 36, "color": INK}},
        "tickfont": {"size": 28, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    margin={"l": 120, "r": 60, "t": 130, "b": 110},
    showlegend=False,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
