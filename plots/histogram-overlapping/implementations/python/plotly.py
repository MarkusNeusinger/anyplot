""" pyplots.ai
histogram-overlapping: Overlapping Histograms
Library: plotly 6.5.0 | Python 3.13.11
Quality: 96/100 | Created: 2025-12-25
"""

import numpy as np
import plotly.graph_objects as go


# Data - heights by gender (realistic scenario showing overlapping distributions)
np.random.seed(42)
male_heights = np.random.normal(175, 7, 200)  # Mean ~175cm, std ~7cm
female_heights = np.random.normal(162, 6, 200)  # Mean ~162cm, std ~6cm

# Create figure
fig = go.Figure()

# Add histograms with semi-transparent fills for overlap visibility
fig.add_trace(
    go.Histogram(
        x=male_heights,
        name="Male",
        marker=dict(color="#306998", line=dict(color="#1a3a52", width=1)),
        opacity=0.5,
        xbins=dict(size=3),
    )
)

fig.add_trace(
    go.Histogram(
        x=female_heights,
        name="Female",
        marker=dict(color="#FFD43B", line=dict(color="#b3940a", width=1)),
        opacity=0.5,
        xbins=dict(size=3),
    )
)

# Use overlay mode for true overlapping histograms
fig.update_layout(barmode="overlay")

# Layout styling for 4800x2700 px output
fig.update_layout(
    title=dict(text="histogram-overlapping · plotly · pyplots.ai", font=dict(size=32), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Height (cm)", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Frequency", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
    ),
    legend=dict(
        font=dict(size=20),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="rgba(0,0,0,0.2)",
        borderwidth=1,
    ),
    template="plotly_white",
    margin=dict(l=100, r=80, t=100, b=100),
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs="cdn")
