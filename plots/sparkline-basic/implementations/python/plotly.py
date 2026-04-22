""" pyplots.ai
sparkline-basic: Basic Sparkline
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - simulate daily sales trend over ~30 days
np.random.seed(42)
base = 100
trend = np.linspace(0, 20, 30)  # Upward trend
noise = np.random.randn(30) * 8
values = base + trend + noise

# Create figure with minimal sparkline layout
fig = go.Figure()

# Main sparkline
fig.add_trace(
    go.Scatter(
        x=list(range(len(values))), y=values, mode="lines", line={"color": "#306998", "width": 4}, hoverinfo="skip"
    )
)

# Highlight min point (red dot)
min_idx = int(np.argmin(values))
fig.add_trace(
    go.Scatter(
        x=[min_idx], y=[values[min_idx]], mode="markers", marker={"color": "#E74C3C", "size": 16}, hoverinfo="skip"
    )
)

# Highlight max point (green dot)
max_idx = int(np.argmax(values))
fig.add_trace(
    go.Scatter(
        x=[max_idx], y=[values[max_idx]], mode="markers", marker={"color": "#27AE60", "size": 16}, hoverinfo="skip"
    )
)

# Highlight first and last points (Python Yellow)
fig.add_trace(
    go.Scatter(
        x=[0, len(values) - 1],
        y=[values[0], values[-1]],
        mode="markers",
        marker={"color": "#FFD43B", "size": 14},
        hoverinfo="skip",
    )
)

# Sparkline layout - no axes, no labels, no gridlines
fig.update_layout(
    title={
        "text": "sparkline-basic · plotly · pyplots.ai",
        "font": {"size": 48},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    xaxis={"visible": False, "showgrid": False, "zeroline": False, "showticklabels": False},
    yaxis={"visible": False, "showgrid": False, "zeroline": False, "showticklabels": False},
    showlegend=False,
    template="plotly_white",
    margin={"l": 100, "r": 100, "t": 200, "b": 100},
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="white",
)

# Save PNG at 4800x2700 (sparkline uses full canvas but aspect ratio is wide)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
