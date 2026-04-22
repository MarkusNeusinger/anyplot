""" pyplots.ai
bar-stacked-labeled: Stacked Bar Chart with Total Labels
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-09
"""

import altair as alt
import pandas as pd


# Data - Quarterly revenue by product category
data = pd.DataFrame(
    {
        "quarter": ["Q1", "Q1", "Q1", "Q2", "Q2", "Q2", "Q3", "Q3", "Q3", "Q4", "Q4", "Q4"],
        "product": ["Software", "Hardware", "Services"] * 4,
        "revenue": [120, 85, 45, 145, 92, 58, 165, 88, 72, 185, 95, 80],
    }
)

# Calculate totals for labels
totals = data.groupby("quarter")["revenue"].sum().reset_index()
totals.columns = ["quarter", "total"]
totals["label"] = totals["total"].apply(lambda x: f"${x}K")

# Create stacked bar chart
bars = (
    alt.Chart(data)
    .mark_bar(strokeWidth=1, stroke="white")
    .encode(
        x=alt.X("quarter:N", title="Quarter", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y("revenue:Q", title="Revenue ($K)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        color=alt.Color(
            "product:N",
            title="Product",
            scale=alt.Scale(domain=["Software", "Hardware", "Services"], range=["#306998", "#FFD43B", "#4DAF4A"]),
            legend=alt.Legend(titleFontSize=20, labelFontSize=18, symbolSize=300),
        ),
        order=alt.Order("product:N", sort="ascending"),
        tooltip=["quarter:N", "product:N", "revenue:Q"],
    )
)

# Total labels above bars
labels = (
    alt.Chart(totals)
    .mark_text(fontSize=22, fontWeight="bold", dy=-15, color="#333333")
    .encode(x=alt.X("quarter:N"), y=alt.Y("total:Q"), text="label:N")
)

# Combine and configure
chart = (
    (bars + labels)
    .properties(
        width=1400,
        height=800,
        title=alt.Title("bar-stacked-labeled · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3])
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
