""" pyplots.ai
slope-basic: Basic Slope Chart (Slopegraph)
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data - Product sales Q1 vs Q4 comparison (10 products showing various patterns)
products = [
    "Laptop Pro",
    "Wireless Earbuds",
    "Smart Watch",
    "Tablet Ultra",
    "Gaming Mouse",
    "Mechanical Keyboard",
    "Webcam HD",
    "USB Hub",
    "Portable SSD",
    "Monitor Stand",
]

# Sales figures in thousands ($K)
sales_q1 = [245, 180, 120, 195, 85, 110, 45, 30, 75, 55]
sales_q4 = [310, 220, 195, 160, 145, 130, 95, 85, 70, 40]

# Color coding by change direction
colors = []
for q1, q4 in zip(sales_q1, sales_q4, strict=True):
    if q4 > q1:
        colors.append("#306998")  # Python Blue for increase
    elif q4 < q1:
        colors.append("#FFD43B")  # Python Yellow for decrease
    else:
        colors.append("#888888")  # Gray for no change

# Create figure
fig = go.Figure()

# Add slope lines for each product
for i, product in enumerate(products):
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[sales_q1[i], sales_q4[i]],
            mode="lines+markers",
            line={"color": colors[i], "width": 3},
            marker={"size": 14},
            name=product,
            showlegend=False,
            hovertemplate=f"{product}<br>Q1: ${sales_q1[i]}K<br>Q4: ${sales_q4[i]}K<extra></extra>",
        )
    )

# Add labels at start points (Q1)
for i, product in enumerate(products):
    fig.add_annotation(
        x=-0.05,
        y=sales_q1[i],
        text=f"{product}: ${sales_q1[i]}K",
        showarrow=False,
        xanchor="right",
        font={"size": 16, "color": colors[i]},
    )

# Add labels at end points (Q4)
for i, product in enumerate(products):
    fig.add_annotation(
        x=1.05,
        y=sales_q4[i],
        text=f"${sales_q4[i]}K: {product}",
        showarrow=False,
        xanchor="left",
        font={"size": 16, "color": colors[i]},
    )

# Layout
fig.update_layout(
    title={
        "text": "Product Sales Q1 vs Q4 · slope-basic · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "tickmode": "array",
        "tickvals": [0, 1],
        "ticktext": ["Q1 2024", "Q4 2024"],
        "tickfont": {"size": 22},
        "range": [-0.4, 1.4],
        "showgrid": False,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Sales ($K)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
        "zeroline": False,
    },
    template="plotly_white",
    margin={"l": 200, "r": 200, "t": 80, "b": 60},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
