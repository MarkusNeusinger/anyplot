""" pyplots.ai
bar-horizontal: Horizontal Bar Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import plotly.graph_objects as go


# Data - Survey results: "What programming language do you use most?"
categories = ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust", "Ruby", "PHP", "Swift"]
# Response counts (sorted descending for visual clarity)
values = [2847, 2156, 1823, 1542, 987, 756, 623, 412, 389, 298]

# Create horizontal bar chart
fig = go.Figure()

fig.add_trace(
    go.Bar(
        y=categories,
        x=values,
        orientation="h",
        marker_color="#306998",
        marker_line={"color": "#1e4266", "width": 1},
        text=values,
        textposition="outside",
        textfont={"size": 32},
    )
)

# Layout for 4800x2700 px
fig.update_layout(
    title={"text": "bar-horizontal · plotly · pyplots.ai", "font": {"size": 40}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Number of Responses", "font": {"size": 40}},
        "tickfont": {"size": 32},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.1)",
        "range": [0, max(values) * 1.15],
    },
    yaxis={
        "title": {"text": "Programming Language", "font": {"size": 40}},
        "tickfont": {"size": 32},
        "autorange": "reversed",
        "showgrid": False,
    },
    template="plotly_white",
    margin={"l": 200, "r": 120, "t": 120, "b": 100},
    bargap=0.3,
)

# Save as PNG (4800x2700)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html")
