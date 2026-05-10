""" anyplot.ai
bar-error: Bar Chart with Error Bars
Library: plotly 6.7.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-10
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

# Data - Lab experiment comparing treatment effectiveness
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D"]
values = np.array([45.2, 62.8, 58.3, 71.5, 55.9])
# Asymmetric errors with more dramatic variation across groups
errors_lower = np.array([3.2, 7.8, 2.9, 8.1, 3.5])
errors_upper = np.array([4.1, 9.2, 3.6, 11.3, 4.8])

# Create figure
fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=categories,
        y=values,
        marker=dict(color=BRAND, line=dict(color=INK_SOFT, width=2)),
        error_y=dict(
            type="data",
            symmetric=False,
            array=errors_upper,
            arrayminus=errors_lower,
            color=INK_SOFT,
            thickness=3,
            width=12,
        ),
        name="Measurement",
        hovertemplate="<b>%{x}</b><br>Value: %{y:.1f}%<br>+%{error_y.array[0]:.1f}% / -%{error_y.arrayminus[0]:.1f}%<extra></extra>",
    )
)

# Layout for 4800x2700 px output
fig.update_layout(
    title=dict(text="bar-error · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Treatment Group", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=False,
        linecolor=INK_SOFT,
        linewidth=1,
    ),
    yaxis=dict(
        title=dict(text="Response Value (%)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        linewidth=1,
        range=[0, 90],
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=True,
    legend=dict(
        x=0.98, y=0.98, bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1, font=dict(size=16, color=INK_SOFT)
    ),
    margin=dict(l=100, r=80, t=120, b=100),
    annotations=[
        dict(
            text="Error bars: ±1 SD (asymmetric)",
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.02,
            xanchor="left",
            yanchor="bottom",
            font=dict(size=14, color=INK_SOFT),
            showarrow=False,
        )
    ],
)

# Save as PNG (4800x2700 px) and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
