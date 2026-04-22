""" pyplots.ai
funnel-basic: Basic Funnel Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data - Sales funnel example
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]

# Colors for each stage - using Python Blue as primary, with variations
colors = ["#306998", "#4682B4", "#5F9EA0", "#6CA6CD", "#FFD43B"]

# Create funnel chart
fig = go.Figure(
    go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        textfont={"size": 20, "color": "white"},
        marker={"color": colors, "line": {"width": 2, "color": "white"}},
        connector={"line": {"color": "gray", "width": 1}},
    )
)

# Update layout for 4800x2700 px output
fig.update_layout(
    title={"text": "funnel-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    yaxis={"title": {"text": "Stage", "font": {"size": 24}}, "tickfont": {"size": 20}},
    xaxis={"title": {"text": "Count", "font": {"size": 24}}, "tickfont": {"size": 18}},
    template="plotly_white",
    margin={"l": 150, "r": 50, "t": 100, "b": 80},
)

# Save as PNG (4800 x 2700 px) and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
