""" pyplots.ai
stem-basic: Basic Stem Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - Discrete signal samples (damped oscillation)
np.random.seed(42)
x = np.arange(0, 30)
y = np.exp(-x / 10) * np.cos(x * 0.8) + np.random.randn(30) * 0.05

# Create figure
fig = go.Figure()

# Add baseline at y=0
fig.add_trace(
    go.Scatter(
        x=[x.min() - 0.5, x.max() + 0.5],
        y=[0, 0],
        mode="lines",
        line={"color": "#333333", "width": 2},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Add stems (vertical lines from baseline to data points)
for xi, yi in zip(x, y, strict=True):
    fig.add_trace(
        go.Scatter(
            x=[xi, xi],
            y=[0, yi],
            mode="lines",
            line={"color": "#306998", "width": 2},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Add markers at the top of each stem
fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        mode="markers",
        marker={"color": "#306998", "size": 16, "line": {"color": "white", "width": 2}},
        showlegend=False,
        hovertemplate="Sample: %{x}<br>Amplitude: %{y:.3f}<extra></extra>",
    )
)

# Update layout for 4800x2700 px
fig.update_layout(
    title={"text": "stem-basic · plotly · pyplots.ai", "font": {"size": 42}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Sample Index", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Amplitude", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "zeroline": False,
    },
    template="plotly_white",
    margin={"l": 120, "r": 60, "t": 130, "b": 110},
    showlegend=False,
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html")
