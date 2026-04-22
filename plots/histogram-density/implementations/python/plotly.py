""" pyplots.ai
histogram-density: Density Histogram
Library: plotly 6.5.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-29
"""

import numpy as np
import plotly.graph_objects as go
from scipy import stats


# Data - simulated test scores with a roughly normal distribution
np.random.seed(42)
test_scores = np.concatenate(
    [
        np.random.normal(loc=72, scale=10, size=400),  # Main group
        np.random.normal(loc=88, scale=5, size=150),  # High performers
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
        marker=dict(color="#306998", line=dict(color="white", width=1)),
        opacity=0.75,
        name="Test Scores",
    )
)

# Overlay KDE (kernel density estimate) for smooth reference curve
x_range = np.linspace(test_scores.min() - 5, test_scores.max() + 5, 200)
kde = stats.gaussian_kde(test_scores)
fig.add_trace(
    go.Scatter(x=x_range, y=kde(x_range), mode="lines", line=dict(color="#FFD43B", width=4), name="Density Curve (KDE)")
)

# Layout
fig.update_layout(
    title=dict(text="histogram-density · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Test Score (points)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Density (probability per unit)", font=dict(size=22)),
        tickfont=dict(size=18),
        showgrid=True,
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    template="plotly_white",
    legend=dict(
        font=dict(size=18),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
    ),
    margin=dict(l=80, r=40, t=80, b=80),
    bargap=0.02,
)

# Save as PNG (4800 x 2700 via scale=3)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
