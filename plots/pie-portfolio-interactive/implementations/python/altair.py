""" pyplots.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import altair as alt
import pandas as pd


# Portfolio data with asset class categories
data = pd.DataFrame(
    {
        "asset": [
            "Apple Inc.",
            "Microsoft",
            "Amazon",
            "Nvidia",
            "US Treasury 10Y",
            "Corporate Bonds",
            "Municipal Bonds",
            "Gold ETF",
            "Real Estate Fund",
            "Commodities",
        ],
        "weight": [15.0, 12.0, 10.0, 8.0, 18.0, 12.0, 5.0, 8.0, 7.0, 5.0],
        "category": [
            "Equities",
            "Equities",
            "Equities",
            "Equities",
            "Fixed Income",
            "Fixed Income",
            "Fixed Income",
            "Alternatives",
            "Alternatives",
            "Alternatives",
        ],
    }
)

# Calculate category totals for drill-down
category_totals = data.groupby("category")["weight"].sum().reset_index()
category_totals.columns = ["category", "total_weight"]

# Merge category totals back to main data
data = data.merge(category_totals, on="category")

# Color scheme by category (Python-inspired colors)
category_colors = alt.Scale(
    domain=["Equities", "Fixed Income", "Alternatives"], range=["#306998", "#FFD43B", "#4B8BBE"]
)

# Selection for interactivity
selection = alt.selection_point(fields=["category"], bind="legend")

# Main donut chart with individual holdings
base = (
    alt.Chart(data)
    .encode(
        theta=alt.Theta("weight:Q", stack=True),
        color=alt.Color(
            "category:N",
            scale=category_colors,
            legend=alt.Legend(title="Asset Class", titleFontSize=20, labelFontSize=18, orient="right", symbolSize=300),
        ),
        opacity=alt.condition(selection, alt.value(1), alt.value(0.3)),
        tooltip=[
            alt.Tooltip("asset:N", title="Holding"),
            alt.Tooltip("weight:Q", title="Weight (%)", format=".1f"),
            alt.Tooltip("category:N", title="Asset Class"),
            alt.Tooltip("total_weight:Q", title="Category Total (%)", format=".1f"),
        ],
    )
    .add_params(selection)
)

# Donut chart with arc marks
donut = base.mark_arc(innerRadius=180, outerRadius=350, stroke="white", strokeWidth=3)

# Text labels for holdings (show weight percentages)
text_labels = base.mark_text(radius=420, fontSize=16, fontWeight="bold").encode(text=alt.Text("weight:Q", format=".1f"))

# Center text showing total
center_text = (
    alt.Chart(pd.DataFrame({"text": ["Portfolio\nAllocation"]}))
    .mark_text(fontSize=24, fontWeight="bold", align="center", baseline="middle", lineBreak="\n", color="#333333")
    .encode(text="text:N")
)

# Combine layers
chart = (
    alt.layer(donut, text_labels, center_text)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "pie-portfolio-interactive \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle", color="#333333"
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_axis(labelFontSize=18, titleFontSize=22)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
