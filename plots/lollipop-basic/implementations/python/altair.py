""" pyplots.ai
lollipop-basic: Basic Lollipop Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import pandas as pd


# Data - Product sales by category, sorted by value
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Beauty",
    "Automotive",
    "Food & Grocery",
    "Pet Supplies",
]
values = [425000, 312000, 287000, 234000, 198000, 176000, 152000, 134000, 118000, 95000]

df = pd.DataFrame({"category": categories, "value": values})

# Sort by value descending for better readability
df = df.sort_values("value", ascending=False).reset_index(drop=True)

# Create stems (vertical lines from baseline to value)
stems = (
    alt.Chart(df)
    .mark_rule(color="#306998", strokeWidth=3)
    .encode(
        x=alt.X(
            "category:N", sort="-y", title="Category", axis=alt.Axis(labelFontSize=16, titleFontSize=20, labelAngle=-45)
        ),
        y=alt.Y("value:Q", title="Sales ($)", axis=alt.Axis(labelFontSize=16, titleFontSize=20)),
    )
)

# Create dots at the top of each stem
dots = (
    alt.Chart(df)
    .mark_circle(color="#306998", size=400)
    .encode(
        x=alt.X("category:N", sort="-y"),
        y=alt.Y("value:Q"),
        tooltip=["category:N", alt.Tooltip("value:Q", format="$,.0f")],
    )
)

# Combine stems and dots
chart = (
    (stems + dots)
    .properties(
        width=1600, height=900, title=alt.Title("lollipop-basic · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(labelFontSize=16, titleFontSize=20, grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3 to get 4800x2700)
chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactive version
chart.save("plot.html")
