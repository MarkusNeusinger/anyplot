""" pyplots.ai
bar-diverging: Diverging Bar Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import altair as alt
import pandas as pd


# Data - Customer satisfaction survey results by department
data = pd.DataFrame(
    {
        "department": [
            "Customer Service",
            "Engineering",
            "Sales",
            "Marketing",
            "HR",
            "Finance",
            "Operations",
            "IT Support",
            "R&D",
            "Quality Assurance",
            "Legal",
            "Logistics",
        ],
        "satisfaction_score": [42, 35, 28, 15, 8, -5, -12, -18, -25, -32, -38, -45],
    }
)

# Add color indicator for positive/negative
data["sentiment"] = data["satisfaction_score"].apply(lambda x: "Positive" if x >= 0 else "Negative")

# Sort by value for better pattern recognition
data = data.sort_values("satisfaction_score", ascending=True)

# Create diverging bar chart
chart = (
    alt.Chart(data)
    .mark_bar(cornerRadius=3, height=35)
    .encode(
        x=alt.X(
            "satisfaction_score:Q",
            title="Net Satisfaction Score",
            axis=alt.Axis(titleFontSize=22, labelFontSize=18, tickCount=10),
            scale=alt.Scale(domain=[-60, 60]),
        ),
        y=alt.Y(
            "department:N",
            title=None,
            sort=alt.EncodingSortField(field="satisfaction_score", order="ascending"),
            axis=alt.Axis(labelFontSize=18),
        ),
        color=alt.Color(
            "sentiment:N",
            scale=alt.Scale(
                domain=["Positive", "Negative"],
                range=["#306998", "#FFD43B"],  # Python Blue for positive, Python Yellow for negative
            ),
            legend=alt.Legend(title="Sentiment", titleFontSize=20, labelFontSize=18, orient="bottom-right", offset=10),
        ),
        tooltip=[alt.Tooltip("department:N", title="Department"), alt.Tooltip("satisfaction_score:Q", title="Score")],
    )
    .properties(
        width=1400, height=800, title=alt.Title("bar-diverging · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
)

# Add zero baseline rule
zero_line = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#333333", strokeWidth=2).encode(x="x:Q")

# Combine chart and zero line
final_chart = (
    (chart + zero_line).configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3]).configure_view(strokeWidth=0)
)

# Save as PNG (scale_factor=3 for 4800x2700 target)
final_chart.save("plot.png", scale_factor=3.0)

# Save as HTML for interactivity
final_chart.save("plot.html")
