""" anyplot.ai
donut-basic: Basic Donut Chart
Library: plotly 6.7.0 | Python 3.14.4
Quality: 89/100 | Updated: 2026-04-24
"""

import plotly.graph_objects as go


# Data - Budget allocation by category
categories = ["Engineering", "Marketing", "Operations", "Sales", "R&D", "HR"]
values = [35, 20, 15, 15, 10, 5]
total = sum(values)

# Colors - Python Blue primary, then colorblind-safe palette
colors = ["#306998", "#FFD43B", "#4ECDC4", "#E07A5F", "#81B29A", "#F4A261"]

# Create donut chart
fig = go.Figure(
    data=[
        go.Pie(
            labels=categories,
            values=values,
            hole=0.5,
            marker={"colors": colors, "line": {"color": "white", "width": 3}},
            textinfo="label+percent",
            textfont={"size": 20},
            textposition="outside",
            pull=[0.02] * len(categories),
        )
    ]
)

# Add center annotation showing total
fig.add_annotation(
    text=f"<b>Total</b><br>${total}M", x=0.5, y=0.5, font={"size": 36, "color": "#306998"}, showarrow=False
)

# Layout for 4800x2700 px
fig.update_layout(
    title={"text": "donut-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    showlegend=True,
    legend={"font": {"size": 20}, "orientation": "v", "yanchor": "middle", "y": 0.5, "xanchor": "left", "x": 1.02},
    template="plotly_white",
    margin={"l": 50, "r": 200, "t": 100, "b": 50},
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
