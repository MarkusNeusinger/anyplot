""" pyplots.ai
line-basic: Basic Line Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - Monthly temperature readings
np.random.seed(42)
months = np.arange(1, 13)
# Simulate temperature pattern (cold winter, warm summer)
temperature = 15 + 12 * np.sin((months - 4) * np.pi / 6) + np.random.randn(12) * 1.5

# Create figure
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=months,
        y=temperature,
        mode="lines+markers",
        line={"color": "#306998", "width": 5},
        marker={"size": 18, "color": "#306998"},
        hovertemplate="Month: %{x}<br>Temperature: %{y:.1f}°C<extra></extra>",
    )
)

# Layout
fig.update_layout(
    title={"text": "line-basic · plotly · pyplots.ai", "font": {"size": 40}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Month", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "tickmode": "array",
        "tickvals": months,
        "ticktext": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
    },
    yaxis={
        "title": {"text": "Temperature (°C)", "font": {"size": 36}},
        "tickfont": {"size": 28},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
    },
    template="plotly_white",
    margin={"t": 120, "b": 100, "l": 120, "r": 50},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
