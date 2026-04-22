""" pyplots.ai
bar-grouped: Grouped Bar Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import altair as alt
import pandas as pd


# Data: Quarterly revenue by product line
data = pd.DataFrame(
    {
        "Quarter": ["Q1", "Q1", "Q1", "Q2", "Q2", "Q2", "Q3", "Q3", "Q3", "Q4", "Q4", "Q4"],
        "Product": ["Software", "Hardware", "Services"] * 4,
        "Revenue": [
            120,
            85,
            45,  # Q1
            145,
            78,
            52,  # Q2
            132,
            92,
            68,  # Q3
            168,
            105,
            75,  # Q4
        ],
    }
)

# Create grouped bar chart
chart = (
    alt.Chart(data)
    .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    .encode(
        x=alt.X("Quarter:O", title="Quarter", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        xOffset="Product:N",
        y=alt.Y("Revenue:Q", title="Revenue (thousands USD)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        color=alt.Color(
            "Product:N",
            scale=alt.Scale(domain=["Software", "Hardware", "Services"], range=["#306998", "#FFD43B", "#4ECDC4"]),
            legend=alt.Legend(
                title="Product Line", titleFontSize=20, labelFontSize=18, orient="top-right", direction="vertical"
            ),
        ),
        tooltip=["Quarter", "Product", "Revenue"],
    )
    .properties(
        width=1600, height=900, title=alt.Title("bar-grouped · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(gridColor="#E0E0E0", gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
