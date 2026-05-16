""" anyplot.ai
histogram-cumulative: Cumulative Histogram
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-11
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

# Data: Simulated test scores with realistic distribution
np.random.seed(42)
scores = np.concatenate(
    [
        np.random.normal(65, 10, 300),  # Average performers
        np.random.normal(85, 5, 150),  # High performers
        np.random.normal(45, 8, 50),  # Low performers
    ]
)
scores = np.clip(scores, 0, 100)

# Calculate cumulative histogram for reference lines
bin_count = 25
counts, bin_edges = np.histogram(scores, bins=bin_count)
cumulative_counts = np.cumsum(counts)
cumulative_proportion = cumulative_counts / len(scores)

# Create figure with native cumulative histogram
fig = go.Figure()

# Add cumulative histogram using Plotly's native cumulative feature
fig.add_trace(
    go.Histogram(
        x=scores,
        nbinsx=bin_count,
        cumulative=dict(enabled=True, direction="increasing"),
        histnorm="percent",
        marker=dict(color=BRAND, line=dict(width=0)),
        name="Cumulative Distribution",
        hovertemplate="Score ≤ %{x:.1f}<br>Proportion: %{y:.2%}<extra></extra>",
    )
)

# Add percentile reference lines
percentiles = [0.25, 0.50, 0.75]
for p in percentiles:
    x_val = np.percentile(scores, p * 100)
    # Vertical line
    fig.add_trace(
        go.Scatter(
            x=[x_val, x_val],
            y=[0, p * 100],
            mode="lines",
            line=dict(color=INK_SOFT, width=2, dash="dash"),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    # Horizontal line
    fig.add_trace(
        go.Scatter(
            x=[0, x_val],
            y=[p * 100, p * 100],
            mode="lines",
            line=dict(color=INK_SOFT, width=2, dash="dash"),
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Add percentile markers
fig.add_trace(
    go.Scatter(
        x=[np.percentile(scores, 25), np.percentile(scores, 50), np.percentile(scores, 75)],
        y=[25, 50, 75],
        mode="markers+text",
        marker=dict(color=BRAND, size=14, line=dict(color=INK, width=2)),
        text=["25%", "50%", "75%"],
        textposition="top right",
        textfont=dict(size=16, color=INK),
        showlegend=False,
        hovertemplate="%{text} of scores ≤ %{x:.1f}<extra></extra>",
    )
)

# Update layout with theme-adaptive styling
fig.update_layout(
    title=dict(
        text="histogram-cumulative · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Test Score (points)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        range=[0, 105],
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Cumulative Proportion (%)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        range=[0, 105],
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    showlegend=True,
    legend=dict(
        x=0.65, y=0.35, font=dict(size=16, color=INK_SOFT), bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1
    ),
    margin=dict(l=80, r=40, t=80, b=80),
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
