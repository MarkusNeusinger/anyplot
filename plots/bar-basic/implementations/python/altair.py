""" pyplots.ai
bar-basic: Basic Bar Chart
Library: altair 6.0.0 | Python 3.14
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import pandas as pd


# Data - Product sales by category (realistic retail scenario)
# Includes close-valued pairs (Clothing/Home & Garden, Toys/Food) to showcase comparison
data = pd.DataFrame(
    {
        "category": ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Food"],
        "value": [45200, 31500, 29800, 21800, 18500, 14200, 13100],
    }
)

# Highlight the top-performing category
data["is_top"] = data["value"] == data["value"].max()

# Sort order by descending value
sort_order = data.sort_values("value", ascending=False)["category"].tolist()

# Chart - bars with conditional color to highlight leader
bars = (
    alt.Chart(data)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X(
            "category:N",
            title="Product Category",
            sort=sort_order,
            axis=alt.Axis(labelAngle=-45, labelFontSize=18, titleFontSize=22),
        ),
        y=alt.Y(
            "value:Q",
            title="Sales ($)",
            scale=alt.Scale(domain=[0, 50000]),
            axis=alt.Axis(
                labelFontSize=18, titleFontSize=22, format="$,.0f", values=[0, 10000, 20000, 30000, 40000, 50000]
            ),
        ),
        color=alt.condition(alt.datum.is_top, alt.value("#FFD43B"), alt.value("#306998")),
        tooltip=[alt.Tooltip("category:N", title="Category"), alt.Tooltip("value:Q", title="Sales", format="$,.0f")],
    )
)

# Value labels above bars
labels = bars.mark_text(align="center", baseline="bottom", dy=-8, fontSize=16, color="#333333").encode(
    text=alt.Text("value:Q", format="$,.0f"), color=alt.value("#333333")
)

# Annotation highlighting top performer
annotation = (
    alt.Chart(pd.DataFrame({"category": ["Electronics"], "value": [45200], "label": ["Top seller — $45.2k"]}))
    .mark_text(align="center", baseline="bottom", dy=-28, fontSize=18, fontWeight="bold", color="#b8860b")
    .encode(x=alt.X("category:N", sort=sort_order), y=alt.Y("value:Q"), text=alt.Text("label:N"))
)

# Combine bars + labels + annotation
chart = (
    (bars + labels + annotation)
    .properties(width=1600, height=900, title=alt.Title(text="bar-basic · altair · pyplots.ai", fontSize=28))
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False)
    .configure_axisY(grid=True, gridOpacity=0.15, gridDash=[4, 4])
)

# Save as PNG (scale_factor=3 gives 4800x2700 at 1600x900)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML
chart.save("plot.html")
