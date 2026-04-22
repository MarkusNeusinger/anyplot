""" pyplots.ai
area-stacked: Stacked Area Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Monthly website traffic sources over 2 years
np.random.seed(42)
months = pd.date_range(start="2023-01", periods=24, freq="ME")

# Generate realistic traffic data with trends
base_direct = 15000 + np.linspace(0, 5000, 24) + np.random.randn(24) * 1000
base_organic = 25000 + np.linspace(0, 15000, 24) + np.random.randn(24) * 2000
base_referral = 8000 + np.linspace(0, 3000, 24) + np.random.randn(24) * 800
base_social = 5000 + np.linspace(0, 8000, 24) + np.random.randn(24) * 1200

# Ensure positive values
direct = np.maximum(base_direct, 1000).astype(int)
organic = np.maximum(base_organic, 1000).astype(int)
referral = np.maximum(base_referral, 500).astype(int)
social = np.maximum(base_social, 500).astype(int)

# Colors - Python Blue first, then harmonious colors
colors = ["#306998", "#FFD43B", "#4CAF50", "#E91E63"]

# Create figure
fig = go.Figure()

# Add traces in order (largest at bottom for stacked area)
fig.add_trace(
    go.Scatter(
        x=months,
        y=organic,
        name="Organic Search",
        mode="lines",
        line=dict(width=0.5, color=colors[0]),
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.7)",
        stackgroup="one",
    )
)

fig.add_trace(
    go.Scatter(
        x=months,
        y=direct,
        name="Direct",
        mode="lines",
        line=dict(width=0.5, color=colors[1]),
        fill="tonexty",
        fillcolor="rgba(255, 212, 59, 0.7)",
        stackgroup="one",
    )
)

fig.add_trace(
    go.Scatter(
        x=months,
        y=social,
        name="Social Media",
        mode="lines",
        line=dict(width=0.5, color=colors[2]),
        fill="tonexty",
        fillcolor="rgba(76, 175, 80, 0.7)",
        stackgroup="one",
    )
)

fig.add_trace(
    go.Scatter(
        x=months,
        y=referral,
        name="Referral",
        mode="lines",
        line=dict(width=0.5, color=colors[3]),
        fill="tonexty",
        fillcolor="rgba(233, 30, 99, 0.7)",
        stackgroup="one",
    )
)

# Layout
fig.update_layout(
    title=dict(
        text="Website Traffic Sources · area-stacked · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Month", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0, 0, 0, 0.1)",
        showgrid=True,
    ),
    yaxis=dict(
        title=dict(text="Monthly Visitors", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0, 0, 0, 0.1)",
        showgrid=True,
        rangemode="tozero",
    ),
    legend=dict(font=dict(size=18), orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    template="plotly_white",
    margin=dict(l=80, r=40, t=120, b=80),
    hovermode="x unified",
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
