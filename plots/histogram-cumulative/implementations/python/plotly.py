"""anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
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

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
PERCENTILES = [25, 50, 75]  # reference levels marked on the curve
N_BINS = 25

# Columns: set these to your table's column names
SCORE = "Test score (points)"  # role: numeric

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
rng = np.random.default_rng(42)
scores = np.clip(
    np.concatenate(
        [
            rng.normal(65, 10, 300),  # average performers
            rng.normal(85, 5, 150),  # high performers
            rng.normal(45, 8, 50),  # low performers
        ]
    ),
    0,
    100,
)
df = pd.DataFrame({SCORE: scores})

# Plot: reads only df and the constants above
values = df[SCORE].dropna()
quantiles = np.percentile(values, PERCENTILES)
x_lo = min(0, values.min())  # left edge of the axis
labels = [f"{p}%" for p in PERCENTILES]

fig = go.Figure()

# Native cumulative histogram, one bar per bin at the running share up to its upper edge
fig.add_trace(
    go.Histogram(
        x=values,
        nbinsx=N_BINS,
        cumulative=dict(enabled=True, direction="increasing"),
        histnorm="percent",
        marker=dict(color=IMPRINT_PALETTE[0], line=dict(width=0)),
        name="Cumulative distribution",
        hovertemplate="Score ≤ %{x:.1f}<br>Cumulative: %{y:.1f}%<extra></extra>",
    )
)

# Percentile guides: dashed drop lines from the curve to both axes
for p, q in zip(PERCENTILES, quantiles, strict=True):
    fig.add_trace(
        go.Scatter(
            x=[q, q, x_lo],
            y=[0, p, p],
            mode="lines",
            line=dict(color=INK_SOFT, width=1.5, dash="dash"),
            showlegend=False,
            hoverinfo="skip",
        )
    )

fig.add_trace(
    go.Scatter(
        x=quantiles,
        y=PERCENTILES,
        mode="markers+text",
        marker=dict(color=IMPRINT_PALETTE[0], size=9, line=dict(color=INK, width=1.5)),
        text=labels,
        textposition="top left",
        textfont=dict(size=11, color=INK),
        showlegend=False,
        hovertemplate="%{text} of scores ≤ %{x:.1f}<extra></extra>",
    )
)

fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    margin=dict(l=80, r=40, t=80, b=60),
    title=dict(text="histogram-cumulative · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5),
    xaxis=dict(
        title=dict(text=SCORE, font=dict(size=13, color=INK)),
        tickfont=dict(size=11, color=INK_SOFT),
        range=[x_lo, values.max() * 1.05],
        showgrid=True,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Cumulative proportion (%)", font=dict(size=13, color=INK)),
        tickfont=dict(size=11, color=INK_SOFT),
        range=[0, 105],
        showgrid=True,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=True,
    legend=dict(
        x=0.02, y=0.97, font=dict(size=11, color=INK_SOFT), bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1
    ),
)

# Output
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
