""" pyplots.ai
radar-multi: Multi-Series Radar Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import plotly.graph_objects as go


# Data - Product comparison across multiple attributes
categories = ["Performance", "Reliability", "Price Value", "Support", "Ease of Use", "Features"]

# Three products with different strengths
product_a = [85, 90, 70, 80, 75, 88]  # Strong overall, premium
product_b = [75, 65, 95, 70, 90, 60]  # Budget-friendly, easy to use
product_c = [95, 75, 60, 85, 65, 92]  # High-performance, feature-rich

# Close the polygon by repeating the first value
categories_closed = categories + [categories[0]]
product_a_closed = product_a + [product_a[0]]
product_b_closed = product_b + [product_b[0]]
product_c_closed = product_c + [product_c[0]]

# Create radar chart
fig = go.Figure()

# Product A - Python Blue
fig.add_trace(
    go.Scatterpolar(
        r=product_a_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.25)",
        line={"color": "#306998", "width": 3},
        name="Product A (Premium)",
        marker={"size": 10},
    )
)

# Product B - Python Yellow
fig.add_trace(
    go.Scatterpolar(
        r=product_b_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(255, 212, 59, 0.25)",
        line={"color": "#FFD43B", "width": 3},
        name="Product B (Budget)",
        marker={"size": 10},
    )
)

# Product C - Teal
fig.add_trace(
    go.Scatterpolar(
        r=product_c_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(38, 166, 154, 0.25)",
        line={"color": "#26A69A", "width": 3},
        name="Product C (Pro)",
        marker={"size": 10},
    )
)

# Layout
fig.update_layout(
    title={"text": "radar-multi · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    polar={
        "radialaxis": {
            "visible": True,
            "range": [0, 100],
            "tickfont": {"size": 16},
            "tickvals": [20, 40, 60, 80, 100],
            "gridcolor": "rgba(0, 0, 0, 0.2)",
            "linecolor": "rgba(0, 0, 0, 0.3)",
        },
        "angularaxis": {"tickfont": {"size": 20}, "linecolor": "rgba(0, 0, 0, 0.3)", "gridcolor": "rgba(0, 0, 0, 0.2)"},
        "bgcolor": "white",
    },
    legend={
        "font": {"size": 18},
        "x": 1.05,
        "y": 0.5,
        "xanchor": "left",
        "yanchor": "middle",
        "bgcolor": "rgba(255, 255, 255, 0.9)",
        "bordercolor": "rgba(0, 0, 0, 0.2)",
        "borderwidth": 1,
    },
    template="plotly_white",
    margin={"l": 100, "r": 200, "t": 100, "b": 100},
    paper_bgcolor="white",
    plot_bgcolor="white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
