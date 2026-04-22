""" pyplots.ai
range-interval: Range Interval Chart
Library: plotly 6.5.1 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import numpy as np
import plotly.graph_objects as go


# Data: Monthly temperature ranges (°C) for a temperate climate city
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Realistic temperature ranges that follow seasonal pattern
base_temps = [-2, 0, 5, 12, 18, 22, 25, 24, 19, 12, 5, 0]
min_temps = [t - np.random.uniform(3, 6) for t in base_temps]
max_temps = [t + np.random.uniform(4, 8) for t in base_temps]

# Create figure
fig = go.Figure()

# Add range bars as vertical lines with markers at endpoints
for i, month in enumerate(months):
    # Range bar (vertical line)
    fig.add_trace(
        go.Scatter(
            x=[month, month],
            y=[min_temps[i], max_temps[i]],
            mode="lines",
            line=dict(color="#306998", width=18),
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Add markers at min points (bottom)
fig.add_trace(
    go.Scatter(
        x=months,
        y=min_temps,
        mode="markers",
        marker=dict(color="#FFD43B", size=18, line=dict(color="#306998", width=3)),
        name="Min Temperature",
        hovertemplate="%{x}<br>Min: %{y:.1f}°C<extra></extra>",
    )
)

# Add markers at max points (top)
fig.add_trace(
    go.Scatter(
        x=months,
        y=max_temps,
        mode="markers",
        marker=dict(color="#FFD43B", size=18, line=dict(color="#306998", width=3)),
        name="Max Temperature",
        hovertemplate="%{x}<br>Max: %{y:.1f}°C<extra></extra>",
    )
)

# Add midpoint markers
midpoints = [(min_temps[i] + max_temps[i]) / 2 for i in range(len(months))]
fig.add_trace(
    go.Scatter(
        x=months,
        y=midpoints,
        mode="markers",
        marker=dict(color="white", size=10, line=dict(color="#306998", width=2)),
        name="Midpoint",
        hovertemplate="%{x}<br>Mid: %{y:.1f}°C<extra></extra>",
    )
)

# Update layout
fig.update_layout(
    title=dict(text="range-interval · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Month", font=dict(size=22)),
        tickfont=dict(size=18),
        categoryorder="array",
        categoryarray=months,
    ),
    yaxis=dict(
        title=dict(text="Temperature (°C)", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        zeroline=True,
        zerolinecolor="rgba(0,0,0,0.3)",
        zerolinewidth=2,
    ),
    template="plotly_white",
    legend=dict(font=dict(size=16), x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.8)"),
    margin=dict(l=80, r=40, t=80, b=60),
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
