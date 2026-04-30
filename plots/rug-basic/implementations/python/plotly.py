""" anyplot.ai
rug-basic: Basic Rug Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-04-30
"""

import os

import numpy as np
import plotly.graph_objects as go
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data — bimodal distribution to show clustering patterns and gaps
np.random.seed(42)
group1 = np.random.normal(loc=25, scale=5, size=80)
group2 = np.random.normal(loc=55, scale=8, size=60)
gap_region = np.array([38, 42])
values = np.concatenate([group1, group2, gap_region])

# KDE density curve
x_kde = np.linspace(values.min() - 5, values.max() + 5, 400)
kde = stats.gaussian_kde(values, bw_method="scott")
density = kde(x_kde)
rug_y = np.full_like(values, -density.max() * 0.06)

# Figure
fig = go.Figure()

# Filled KDE density curve
fig.add_trace(
    go.Scatter(
        x=x_kde,
        y=density,
        mode="lines",
        line=dict(color=BRAND, width=3),
        fill="tozeroy",
        fillcolor="rgba(0,158,115,0.15)",
        name="Density (KDE)",
        hovertemplate="Response Time: %{x:.1f} ms<br>Density: %{y:.4f}<extra></extra>",
    )
)

# Rug ticks — individual observations as vertical marks below x-axis
fig.add_trace(
    go.Scatter(
        x=values,
        y=rug_y,
        mode="markers",
        marker=dict(symbol="line-ns", size=30, line=dict(width=2, color=BRAND), color=BRAND),
        opacity=0.5,
        name="Observations",
        hovertemplate="Response Time: %{x:.2f} ms<extra></extra>",
    )
)

# Layout
fig.update_layout(
    title=dict(text="rug-basic · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Response Time (ms)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        linecolor=INK_SOFT,
        showline=True,
    ),
    yaxis=dict(
        title=dict(text="Density", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=False,
        zeroline=True,
        zerolinecolor=INK_SOFT,
        zerolinewidth=1,
        range=[-density.max() * 0.15, density.max() * 1.15],
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1, font=dict(size=16, color=INK_SOFT), x=0.78, y=0.95
    ),
    margin=dict(l=100, r=80, t=120, b=100),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
