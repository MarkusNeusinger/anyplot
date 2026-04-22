""" pyplots.ai
area-stacked-percent: 100% Stacked Area Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Energy source mix evolution (percentage of total)
np.random.seed(42)
years = list(range(2015, 2025))

# Start with base percentages and evolve them (showing transition from fossil to renewables)
coal = [45, 42, 39, 35, 32, 28, 25, 22, 19, 16]
natural_gas = [25, 26, 27, 28, 29, 30, 31, 31, 30, 28]
nuclear = [12, 12, 12, 12, 12, 12, 12, 12, 12, 12]
renewables = [18, 20, 22, 25, 27, 30, 32, 35, 39, 44]

# Create DataFrame in long format for Altair
data = []
for i, year in enumerate(years):
    data.append({"Year": year, "Source": "Coal", "Percentage": coal[i]})
    data.append({"Year": year, "Source": "Natural Gas", "Percentage": natural_gas[i]})
    data.append({"Year": year, "Source": "Nuclear", "Percentage": nuclear[i]})
    data.append({"Year": year, "Source": "Renewables", "Percentage": renewables[i]})

df = pd.DataFrame(data)

# Define category order for stacking (bottom to top) using numeric order
source_order = ["Coal", "Natural Gas", "Nuclear", "Renewables"]
stack_order = {"Coal": 1, "Natural Gas": 2, "Nuclear": 3, "Renewables": 4}
df["StackOrder"] = df["Source"].map(stack_order)

# Color palette using Python colors and complementary
colors = ["#306998", "#FFD43B", "#7B68EE", "#2E8B57"]

# Plot - 100% Stacked Area Chart
chart = (
    alt.Chart(df)
    .mark_area(opacity=0.85, line=alt.MarkConfig(strokeWidth=2))
    .encode(
        x=alt.X("Year:O", title="Year", axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0)),
        y=alt.Y(
            "Percentage:Q",
            title="Share of Energy Mix (%)",
            stack="normalize",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, format=".0%"),
        ),
        color=alt.Color(
            "Source:N",
            scale=alt.Scale(domain=source_order, range=colors),
            legend=alt.Legend(
                title="Energy Source",
                titleFontSize=20,
                labelFontSize=18,
                orient="right",
                symbolSize=300,
                symbolStrokeWidth=0,
            ),
        ),
        order=alt.Order("StackOrder:Q", sort="ascending"),
        tooltip=[
            alt.Tooltip("Year:O", title="Year"),
            alt.Tooltip("Source:N", title="Source"),
            alt.Tooltip("Percentage:Q", title="Share", format=".1f"),
        ],
    )
    .properties(
        width=1400,
        height=800,
        title=alt.Title(text="area-stacked-percent · altair · pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(grid=True, gridOpacity=0.3, gridDash=[4, 4])
    .configure_view(strokeWidth=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.interactive().save("plot.html")
