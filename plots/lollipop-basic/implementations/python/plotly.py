""" pyplots.ai
lollipop-basic: Basic Lollipop Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data - Product sales by category, sorted by value
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Beauty",
    "Automotive",
    "Food & Grocery",
    "Health",
]
values = [125000, 98000, 87000, 76000, 65000, 54000, 48000, 42000, 38000, 31000]

# Create figure
fig = go.Figure()

# Add stems (thin lines from baseline to value)
for cat, val in zip(categories, values, strict=True):
    fig.add_trace(
        go.Scatter(
            x=[cat, cat],
            y=[0, val],
            mode="lines",
            line={"color": "#306998", "width": 3},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Add markers (dots at the top of each stem)
fig.add_trace(
    go.Scatter(
        x=categories,
        y=values,
        mode="markers",
        marker={"color": "#306998", "size": 18, "line": {"color": "white", "width": 2}},
        showlegend=False,
        hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
    )
)

# Update layout for 4800x2700 px
fig.update_layout(
    title={"text": "lollipop-basic · plotly · pyplots.ai", "font": {"size": 40}, "x": 0.5, "xanchor": "center"},
    xaxis={"title": {"text": "Product Category", "font": {"size": 40}}, "tickfont": {"size": 32}, "tickangle": -45},
    yaxis={
        "title": {"text": "Sales ($)", "font": {"size": 40}},
        "tickfont": {"size": 32},
        "tickformat": "$,.0f",
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
        "range": [0, max(values) * 1.1],
    },
    template="plotly_white",
    margin={"l": 100, "r": 50, "t": 120, "b": 150},
    showlegend=False,
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html")
