""" pyplots.ai
bar-horizontal: Horizontal Bar Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-25
"""

import altair as alt
import pandas as pd


# Data: Top 10 programming languages by popularity (realistic scenario)
data = pd.DataFrame(
    {
        "language": ["Python", "JavaScript", "Java", "C++", "C#", "TypeScript", "Go", "Rust", "Swift", "Kotlin"],
        "popularity": [28.5, 18.2, 15.8, 10.3, 8.7, 6.2, 4.8, 3.5, 2.4, 1.6],
    }
)

# Sort by popularity for better readability
data = data.sort_values("popularity", ascending=True)

# Create horizontal bar chart
chart = (
    alt.Chart(data)
    .mark_bar(
        color="#306998",  # Python Blue
        cornerRadiusEnd=4,
    )
    .encode(
        x=alt.X("popularity:Q", title="Popularity (%)", axis=alt.Axis(labelFontSize=18, titleFontSize=22)),
        y=alt.Y(
            "language:N",
            title="Programming Language",
            sort="-x",  # Sort by x value descending
            axis=alt.Axis(labelFontSize=18, titleFontSize=22),
        ),
        tooltip=[
            alt.Tooltip("language:N", title="Language"),
            alt.Tooltip("popularity:Q", title="Popularity (%)", format=".1f"),
        ],
    )
    .properties(
        width=1400, height=850, title=alt.Title("bar-horizontal · altair · pyplots.ai", fontSize=28, anchor="middle")
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[3, 3])
    .configure_view(strokeWidth=0)
)

# Save as PNG (1400 × 3 = 4200, ~4800 with margins; 850 × 3 = 2550, ~2700 with margins)
chart.save("plot.png", scale_factor=3.0)

# Save as interactive HTML
chart.save("plot.html")
