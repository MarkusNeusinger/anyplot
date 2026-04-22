""" pyplots.ai
dumbbell-basic: Basic Dumbbell Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import pandas as pd


# Data - Employee satisfaction scores before and after policy changes
# Sorted by improvement (difference) to reveal patterns
data = pd.DataFrame(
    {
        "category": [
            "Customer Support",
            "Engineering",
            "Sales",
            "Marketing",
            "HR",
            "Finance",
            "Operations",
            "Legal",
            "R&D",
            "IT",
        ],
        "before": [52, 61, 58, 65, 72, 68, 55, 74, 63, 59],
        "after": [78, 82, 76, 81, 85, 79, 64, 81, 69, 64],
    }
)

# Calculate difference and sort by improvement
data["difference"] = data["after"] - data["before"]
data = data.sort_values("difference", ascending=True)

# Reshape data for Altair (long format for dots)
dots_data = pd.melt(
    data, id_vars=["category", "difference"], value_vars=["before", "after"], var_name="period", value_name="score"
)

# Shared scale for x-axis
x_scale = alt.Scale(domain=[45, 90])

# Create the connecting lines (using before/after as x values for line)
lines = (
    alt.Chart(data)
    .mark_rule(strokeWidth=2, color="#999999")
    .encode(
        y=alt.Y(
            "category:N",
            sort=alt.EncodingSortField(field="difference", order="ascending"),
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, title=None),
        ),
        x=alt.X("before:Q", scale=x_scale),
        x2=alt.X2("after:Q"),
    )
)

# Create the dots with colors for before/after
dots = (
    alt.Chart(dots_data)
    .mark_circle(size=350)
    .encode(
        y=alt.Y("category:N", sort=alt.EncodingSortField(field="difference", order="ascending")),
        x=alt.X(
            "score:Q", axis=alt.Axis(labelFontSize=18, titleFontSize=22), title="Satisfaction Score", scale=x_scale
        ),
        color=alt.Color(
            "period:N",
            scale=alt.Scale(domain=["before", "after"], range=["#306998", "#FFD43B"]),
            legend=alt.Legend(title="Period", labelFontSize=16, titleFontSize=18),
        ),
        tooltip=["category:N", "period:N", "score:Q"],
    )
)

# Combine lines and dots
chart = (
    (lines + dots)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("Employee Satisfaction · dumbbell-basic · altair · pyplots.ai", fontSize=28),
    )
    .configure_view(strokeWidth=0)
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
