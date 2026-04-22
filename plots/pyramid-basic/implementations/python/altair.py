""" pyplots.ai
pyramid-basic: Basic Pyramid Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import pandas as pd


# Data - Population pyramid showing age distribution by gender
age_groups = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
male = [4.8, 5.2, 6.1, 7.3, 8.5, 7.8, 5.9, 3.2, 1.2]  # Millions
female = [4.5, 5.0, 6.3, 7.5, 8.7, 8.2, 6.4, 4.1, 2.1]  # Millions

# Create dataframe with negative values for male (left side)
df = pd.DataFrame(
    {
        "Age Group": age_groups * 2,
        "Population": [-v for v in male] + female,
        "Gender": ["Male"] * len(age_groups) + ["Female"] * len(age_groups),
        "Absolute": male + female,
    }
)

# Sort order: youngest at bottom, oldest at top (traditional pyramid)
age_order = list(reversed(age_groups))

# Create pyramid chart with color encoding for legend
chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        y=alt.Y("Age Group:N", sort=age_order, axis=alt.Axis(title="Age Group", titleFontSize=22, labelFontSize=18)),
        x=alt.X(
            "Population:Q",
            axis=alt.Axis(
                title="Population (millions)",
                titleFontSize=22,
                labelFontSize=18,
                values=[-8, -6, -4, -2, 0, 2, 4, 6, 8],
                labelExpr="abs(datum.value)",
            ),
            scale=alt.Scale(domain=[-10, 10]),
        ),
        color=alt.Color(
            "Gender:N",
            scale=alt.Scale(domain=["Male", "Female"], range=["#306998", "#FFD43B"]),
            legend=alt.Legend(title="Gender", titleFontSize=20, labelFontSize=18, orient="top-right"),
        ),
        tooltip=[
            alt.Tooltip("Gender:N"),
            alt.Tooltip("Age Group:N"),
            alt.Tooltip("Absolute:Q", title="Population (M)", format=".1f"),
        ],
    )
    .properties(
        width=1600,
        height=900,
        title=alt.Title(text="pyramid-basic · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_legend(titleFontSize=20, labelFontSize=18)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
