""" pyplots.ai
errorbar-basic: Basic Error Bar Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - experimental measurements with uncertainty
np.random.seed(42)
groups = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
x_positions = list(range(len(groups)))
means = np.array([42.3, 51.7, 63.2, 47.8, 72.4, 58.9])
# Varying error magnitudes to show different precision levels
errors = np.array([5.2, 7.8, 4.1, 9.3, 3.6, 6.5])

# Create figure with scatter points and error bars
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=x_positions,
        y=means,
        mode="markers",
        marker=dict(size=28, color="#306998", line=dict(color="#1e4a6e", width=3)),
        error_y=dict(type="data", array=errors, visible=True, thickness=4, width=16, color="#306998"),
        name="Mean ± SE",
    )
)

# Layout configuration for 4800x2700
fig.update_layout(
    title=dict(text="errorbar-basic · plotly · pyplots.ai", font=dict(size=48), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Experimental Group", font=dict(size=36)),
        tickfont=dict(size=28),
        tickmode="array",
        tickvals=x_positions,
        ticktext=groups,
        showgrid=False,
    ),
    yaxis=dict(
        title=dict(text="Response Value (units)", font=dict(size=36)),
        tickfont=dict(size=28),
        gridcolor="rgba(128,128,128,0.3)",
        gridwidth=1,
        range=[0, 90],
    ),
    template="plotly_white",
    margin=dict(l=140, r=80, t=120, b=120),
    showlegend=True,
    legend=dict(font=dict(size=24), x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.8)"),
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
