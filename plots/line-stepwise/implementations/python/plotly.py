""" pyplots.ai
line-stepwise: Step Line Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 98/100 | Created: 2025-12-30
"""

import numpy as np
import plotly.graph_objects as go


# Data - Server response time monitoring (discrete state changes)
np.random.seed(42)
hours = np.arange(0, 24, 1)
response_times = np.array(
    [
        45,
        45,
        42,
        42,
        48,
        55,
        65,
        72,
        78,
        82,  # Morning ramp-up
        80,
        75,
        85,
        90,
        88,
        85,
        78,
        65,
        55,
        50,  # Afternoon peak
        48,
        45,
        44,
        43,  # Evening decline
    ]
)

# Create step line plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=hours,
        y=response_times,
        mode="lines+markers",
        line=dict(
            shape="hv",  # Step: horizontal then vertical
            color="#306998",
            width=4,
        ),
        marker=dict(size=14, color="#306998", line=dict(color="white", width=2)),
        name="Response Time",
        hovertemplate="Hour: %{x}<br>Response: %{y} ms<extra></extra>",
    )
)

# Layout
fig.update_layout(
    title=dict(text="line-stepwise · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Hour of Day", font=dict(size=22)),
        tickfont=dict(size=18),
        tickmode="linear",
        tick0=0,
        dtick=2,
        range=[-0.5, 23.5],
        showgrid=True,
        gridcolor="rgba(128, 128, 128, 0.2)",
        gridwidth=1,
    ),
    yaxis=dict(
        title=dict(text="Response Time (ms)", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[35, 95],
        showgrid=True,
        gridcolor="rgba(128, 128, 128, 0.2)",
        gridwidth=1,
    ),
    template="plotly_white",
    showlegend=False,
    margin=dict(l=100, r=80, t=120, b=100),
    plot_bgcolor="white",
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
