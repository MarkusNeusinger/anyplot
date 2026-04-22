""" pyplots.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: plotly 6.5.1 | Python 3.13.11
Quality: 95/100 | Created: 2026-01-09
"""

import numpy as np
import plotly.graph_objects as go


# Data: Quarterly revenue by product category
np.random.seed(42)
quarters = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025"]
products = ["Software", "Hardware", "Services", "Maintenance"]

# Revenue data in thousands (realistic business scenario)
revenue_data = {
    "Software": [180, 210, 195, 240, 260],
    "Hardware": [120, 95, 110, 130, 105],
    "Services": [85, 90, 105, 115, 125],
    "Maintenance": [45, 50, 52, 55, 60],
}

# Calculate totals for labels
totals = [sum(revenue_data[p][i] for p in products) for i in range(len(quarters))]

# Colors - Python Blue primary, then complementary colors
colors = ["#306998", "#FFD43B", "#4ECDC4", "#E07A5F"]

# Create figure
fig = go.Figure()

# Add stacked bars for each product
for product, color in zip(products, colors, strict=True):
    fig.add_trace(
        go.Bar(
            name=product,
            x=quarters,
            y=revenue_data[product],
            marker_color=color,
            text=[f"${v}K" for v in revenue_data[product]],
            textposition="inside",
            textfont={"size": 14, "color": "white"},
            insidetextanchor="middle",
        )
    )

# Add total labels as annotations above each bar stack
for quarter, total in zip(quarters, totals, strict=True):
    fig.add_annotation(
        x=quarter,
        y=total + 15,  # Position above the bar
        text=f"<b>${total}K</b>",
        showarrow=False,
        font={"size": 18, "color": "#333333"},
        yanchor="bottom",
    )

# Layout for 4800x2700 px output
fig.update_layout(
    title={"text": "bar-stacked-labeled · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={"title": {"text": "Quarter", "font": {"size": 22}}, "tickfont": {"size": 18}},
    yaxis={
        "title": {"text": "Revenue ($ thousands)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [0, max(totals) + 60],  # Leave space for total labels
        "gridcolor": "rgba(0,0,0,0.1)",
    },
    barmode="stack",
    template="plotly_white",
    legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5, "font": {"size": 16}},
    margin={"t": 120, "b": 80, "l": 80, "r": 40},
)

# Save as PNG (4800x2700)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
