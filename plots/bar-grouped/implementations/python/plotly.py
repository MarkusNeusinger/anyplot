""" pyplots.ai
bar-grouped: Grouped Bar Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import plotly.graph_objects as go


# Data: Quarterly revenue by product line (realistic business scenario)
categories = ["Q1", "Q2", "Q3", "Q4"]
products = {"Electronics": [245, 312, 287, 398], "Clothing": [189, 156, 201, 234], "Home & Garden": [98, 145, 178, 156]}

# Create figure
fig = go.Figure()

# Colors: Python Blue, Python Yellow, then additional colorblind-safe
colors = ["#306998", "#FFD43B", "#E17055"]

# Add bars for each product group
for i, (product, values) in enumerate(products.items()):
    fig.add_trace(
        go.Bar(
            name=product,
            x=categories,
            y=values,
            marker_color=colors[i],
            text=values,
            textposition="outside",
            textfont={"size": 16},
        )
    )

# Layout for 4800x2700 px canvas
fig.update_layout(
    title={"text": "bar-grouped · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={"title": {"text": "Quarter", "font": {"size": 24}}, "tickfont": {"size": 20}},
    yaxis={
        "title": {"text": "Revenue ($ thousands)", "font": {"size": 24}},
        "tickfont": {"size": 20},
        "gridcolor": "rgba(0,0,0,0.1)",
        "gridwidth": 1,
    },
    barmode="group",
    bargap=0.2,
    bargroupgap=0.1,
    template="plotly_white",
    legend={"font": {"size": 20}, "orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5},
    margin={"l": 80, "r": 40, "t": 120, "b": 80},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
