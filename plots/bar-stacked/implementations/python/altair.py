""" pyplots.ai
bar-stacked: Stacked Bar Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import altair as alt
import pandas as pd


# Data: Quarterly sales by product category
data = pd.DataFrame(
    {
        "Quarter": ["Q1", "Q1", "Q1", "Q1", "Q2", "Q2", "Q2", "Q2", "Q3", "Q3", "Q3", "Q3", "Q4", "Q4", "Q4", "Q4"],
        "Product": [
            "Electronics",
            "Clothing",
            "Home & Garden",
            "Sports",
            "Electronics",
            "Clothing",
            "Home & Garden",
            "Sports",
            "Electronics",
            "Clothing",
            "Home & Garden",
            "Sports",
            "Electronics",
            "Clothing",
            "Home & Garden",
            "Sports",
        ],
        "Sales": [85, 62, 45, 38, 92, 71, 52, 44, 78, 65, 48, 41, 110, 88, 68, 55],
    }
)

# Define category order (largest at bottom) and colorblind-safe palette
category_order = ["Electronics", "Clothing", "Home & Garden", "Sports"]
# Using colorblind-safe palette: blue, orange, teal, gold
colors = ["#306998", "#E69F00", "#009E73", "#F0E442"]

# Add order column for stacking (largest at bottom = lower order number)
order_map = {cat: i for i, cat in enumerate(category_order)}
data["color_order"] = data["Product"].map(order_map)

# Calculate totals for each quarter (for labels above stacks)
totals = data.groupby("Quarter")["Sales"].sum().reset_index()
totals.columns = ["Quarter", "Total"]

# Create stacked bar chart
bars = (
    alt.Chart(data)
    .mark_bar(stroke="white", strokeWidth=1.5)
    .encode(
        x=alt.X("Quarter:O", title="Quarter", axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0)),
        y=alt.Y("sum(Sales):Q", title="Sales (Thousands USD)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        color=alt.Color(
            "Product:N",
            title="Product Category",
            scale=alt.Scale(domain=category_order, range=colors),
            legend=alt.Legend(
                titleFontSize=20, labelFontSize=18, symbolSize=400, orient="right", titlePadding=10, labelLimit=200
            ),
        ),
        order=alt.Order("color_order:Q", sort="ascending"),
        tooltip=["Quarter:O", "Product:N", alt.Tooltip("Sales:Q", title="Sales (K USD)")],
    )
)

# Add total value labels above each stack
text = (
    alt.Chart(totals)
    .mark_text(fontSize=18, fontWeight="bold", dy=-12, color="#333333")
    .encode(x=alt.X("Quarter:O"), y=alt.Y("Total:Q"), text=alt.Text("Total:Q", format=".0f"))
)

# Combine bars and labels
chart = (
    (bars + text)
    .properties(
        width=1400, height=850, title=alt.Title("bar-stacked · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
