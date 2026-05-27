""" anyplot.ai
histogram-density: Density Histogram
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-11
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

BRAND = "#009E73"  # Okabe-Ito position 1
OKABE_ITO_2 = "#C475FD"  # Okabe-Ito position 2 for KDE curve

# Data - simulated test scores with a more pronounced bimodal distribution
np.random.seed(42)
test_scores = np.concatenate(
    [
        np.random.normal(loc=65, scale=8, size=350),  # Main group (lower peak)
        np.random.normal(loc=90, scale=6, size=200),  # High performers (upper peak)
    ]
)

# Create histogram with density normalization
fig = go.Figure()

# Histogram trace (normalized to density)
fig.add_trace(
    go.Histogram(
        x=test_scores,
        histnorm="probability density",
        nbinsx=30,
        marker={"color": BRAND, "line": {"color": PAGE_BG, "width": 1}},
        opacity=0.75,
        name="Test Scores",
        hovertemplate="<b>Score Range</b>: %{x:.1f}<br><b>Density</b>: %{y:.4f}<extra></extra>",
    )
)

# Overlay KDE (kernel density estimate) for smooth reference curve
x_range = np.linspace(test_scores.min() - 5, test_scores.max() + 5, 200)
kde = stats.gaussian_kde(test_scores)
fig.add_trace(
    go.Scatter(
        x=x_range,
        y=kde(x_range),
        mode="lines",
        line={"color": OKABE_ITO_2, "width": 4},
        name="Density Curve (KDE)",
        hovertemplate="<b>Score</b>: %{x:.1f}<br><b>Density</b>: %{y:.4f}<extra></extra>",
    )
)

# Layout
fig.update_layout(
    title={"text": "histogram-density · plotly · anyplot.ai", "font": {"size": 28, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Test Score (points)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Density (probability per unit)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 18, "color": INK_SOFT},
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 80},
    bargap=0.02,
    hovermode="closest",
)

# Save as PNG (4800 x 2700 via scale=3)
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
