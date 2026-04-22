""" pyplots.ai
bar-error: Bar Chart with Error Bars
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-27
"""

import numpy as np
import plotly.graph_objects as go


# Data - Lab experiment comparing treatment effectiveness
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D"]
values = np.array([45.2, 62.8, 58.3, 71.5, 55.9])
# Asymmetric errors to show realistic experimental variation
errors_lower = np.array([4.2, 5.8, 3.9, 6.1, 4.5])
errors_upper = np.array([5.1, 7.2, 4.6, 8.3, 5.8])

# Create figure
fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=categories,
        y=values,
        marker=dict(color="#306998", line=dict(color="#1e4d6b", width=2)),
        error_y=dict(
            type="data",
            symmetric=False,
            array=errors_upper,
            arrayminus=errors_lower,
            color="#333333",
            thickness=3,
            width=12,  # Cap width
        ),
        name="Measurement",
    )
)

# Layout for 4800x2700 px output
fig.update_layout(
    title=dict(
        text="Lab Treatment Results · bar-error · plotly · pyplots.ai",
        font=dict(size=32, color="#333333"),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(title=dict(text="Treatment Group", font=dict(size=24)), tickfont=dict(size=20), showgrid=False),
    yaxis=dict(
        title=dict(text="Response Value (%)", font=dict(size=24)),
        tickfont=dict(size=20),
        gridcolor="rgba(0,0,0,0.1)",
        gridwidth=1,
        range=[0, 90],
    ),
    template="plotly_white",
    showlegend=False,
    margin=dict(l=100, r=80, t=120, b=100),
    annotations=[
        dict(
            text="Error bars: ±1 SD (asymmetric)",
            xref="paper",
            yref="paper",
            x=0.98,
            y=0.98,
            xanchor="right",
            yanchor="top",
            font=dict(size=18, color="#666666"),
            showarrow=False,
        )
    ],
)

# Save as PNG (4800x2700 px) and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
