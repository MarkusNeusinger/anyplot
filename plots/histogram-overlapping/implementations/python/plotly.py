""" anyplot.ai
histogram-overlapping: Overlapping Histograms
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-08
"""

import os

import numpy as np
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD"]

# Data - heights by gender (realistic scenario showing overlapping distributions)
np.random.seed(42)
male_heights = np.random.normal(175, 7, 200)
female_heights = np.random.normal(162, 6, 200)

# Create figure
fig = go.Figure()

# Add histograms with semi-transparent fills for overlap visibility
fig.add_trace(
    go.Histogram(
        x=male_heights,
        name="Male",
        marker=dict(color=IMPRINT[0], line=dict(color=INK_SOFT, width=1)),
        opacity=0.5,
        xbins=dict(size=3),
    )
)

fig.add_trace(
    go.Histogram(
        x=female_heights,
        name="Female",
        marker=dict(color=IMPRINT[1], line=dict(color=INK_SOFT, width=1)),
        opacity=0.5,
        xbins=dict(size=3),
    )
)

# Use overlay mode for true overlapping histograms
fig.update_layout(barmode="overlay")

# Layout styling for 4800x2700 px output
fig.update_layout(
    title=dict(
        text="histogram-overlapping · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Height (cm)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Frequency", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    legend=dict(
        font=dict(size=16, color=INK_SOFT),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=100, r=80, t=100, b=100),
)

# Save as PNG (4800 x 2700 px)
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
