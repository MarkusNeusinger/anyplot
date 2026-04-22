""" pyplots.ai
bar-diverging: Diverging Bar Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import plotly.graph_objects as go


# Data: Customer satisfaction survey results by department
# Scores range from -100 (very dissatisfied) to +100 (very satisfied)
categories = [
    "Customer Support",
    "Product Quality",
    "Delivery Speed",
    "Website Experience",
    "Return Policy",
    "Price Value",
    "Mobile App",
    "Payment Options",
    "Product Variety",
    "Checkout Process",
]
values = [72, 58, -25, 45, -42, 31, -15, 68, 22, -8]

# Sort by value for better pattern recognition
sorted_data = sorted(zip(categories, values), key=lambda x: x[1])
categories_sorted = [item[0] for item in sorted_data]
values_sorted = [item[1] for item in sorted_data]

# Assign colors: Python Blue for positive, Python Yellow for negative
colors = ["#306998" if v >= 0 else "#FFD43B" for v in values_sorted]

# Create horizontal diverging bar chart
fig = go.Figure()

fig.add_trace(
    go.Bar(
        y=categories_sorted,
        x=values_sorted,
        orientation="h",
        marker=dict(color=colors, line=dict(color="white", width=1)),
        text=[f"{v:+d}" for v in values_sorted],
        textposition="outside",
        textfont=dict(size=16),
    )
)

# Add zero baseline
fig.add_vline(x=0, line=dict(color="#333333", width=2))

# Layout styling for 4800x2700
fig.update_layout(
    title=dict(
        text="Customer Satisfaction Survey · bar-diverging · plotly · pyplots.ai",
        font=dict(size=28),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="Satisfaction Score", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[-100, 100],
        dtick=25,
        gridcolor="rgba(0,0,0,0.1)",
        zeroline=False,
    ),
    yaxis=dict(title=dict(text="Department", font=dict(size=22)), tickfont=dict(size=18), automargin=True),
    template="plotly_white",
    showlegend=False,
    margin=dict(l=20, r=100, t=80, b=60),
    bargap=0.3,
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
