""" pyplots.ai
waterfall-basic: Basic Waterfall Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 97/100 | Created: 2025-12-24
"""

import plotly.graph_objects as go


# Data - Quarterly financial breakdown from revenue to net income
categories = ["Revenue", "Product Costs", "Operating Expenses", "Marketing", "Other Income", "Taxes", "Net Income"]

# Values: positive for increases, negative for decreases
# Revenue is the starting total, Net Income is the ending total
values = [500000, -180000, -95000, -45000, 25000, -51250, 153750]

# Define measure types: absolute for start, relative for changes, total for end
measures = ["absolute", "relative", "relative", "relative", "relative", "relative", "total"]

# Create waterfall chart using Plotly's native Waterfall trace
fig = go.Figure(
    go.Waterfall(
        name="Financial Breakdown",
        orientation="v",
        measure=measures,
        x=categories,
        y=values,
        textposition="outside",
        text=[f"${abs(v):,.0f}" for v in values],
        textfont={"size": 18},
        connector={"line": {"color": "#888888", "width": 2, "dash": "dot"}},
        decreasing={"marker": {"color": "#e74c3c"}},
        increasing={"marker": {"color": "#2ecc71"}},
        totals={"marker": {"color": "#306998"}},
    )
)

# Update layout for 4800x2700 px canvas
fig.update_layout(
    title={"text": "waterfall-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    xaxis={"title": {"text": "Category", "font": {"size": 24}}, "tickfont": {"size": 18}},
    yaxis={
        "title": {"text": "Amount ($)", "font": {"size": 24}},
        "tickfont": {"size": 18},
        "tickformat": "$,.0f",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
    },
    template="plotly_white",
    showlegend=False,
    margin={"t": 100, "b": 80, "l": 120, "r": 50},
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
