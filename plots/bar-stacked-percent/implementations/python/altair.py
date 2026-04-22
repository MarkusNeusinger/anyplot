""" pyplots.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 98/100 | Created: 2025-12-25
"""

import altair as alt
import pandas as pd


# Data - Energy mix by country (proportions normalized to 100%)
data = pd.DataFrame(
    {
        "Country": [
            "USA",
            "USA",
            "USA",
            "USA",
            "China",
            "China",
            "China",
            "China",
            "Germany",
            "Germany",
            "Germany",
            "Germany",
            "Brazil",
            "Brazil",
            "Brazil",
            "Brazil",
            "India",
            "India",
            "India",
            "India",
        ],
        "Source": ["Fossil Fuels", "Nuclear", "Renewables", "Hydro"] * 5,
        "Value": [
            60,
            18,
            15,
            7,  # USA
            65,
            5,
            18,
            12,  # China
            40,
            12,
            38,
            10,  # Germany
            15,
            3,
            12,
            70,  # Brazil
            72,
            3,
            18,
            7,
        ],  # India
    }
)

# Define color scheme - Python Blue, Python Yellow, and colorblind-safe additions
color_scale = alt.Scale(
    domain=["Fossil Fuels", "Nuclear", "Renewables", "Hydro"], range=["#306998", "#FFD43B", "#2ca02c", "#17becf"]
)

# Create 100% stacked bar chart
chart = (
    alt.Chart(data)
    .mark_bar(stroke="white", strokeWidth=1)
    .encode(
        x=alt.X("Country:N", axis=alt.Axis(labelFontSize=18, titleFontSize=22, labelAngle=0), title="Country"),
        y=alt.Y(
            "Value:Q",
            stack="normalize",
            axis=alt.Axis(labelFontSize=18, titleFontSize=22, format="%"),
            title="Share of Energy Mix",
        ),
        color=alt.Color(
            "Source:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Energy Source",
                titleFontSize=18,
                labelFontSize=16,
                orient="right",
                symbolSize=200,
                symbolStrokeWidth=0,
            ),
        ),
        order=alt.Order("Source:N", sort="descending"),
        tooltip=[
            alt.Tooltip("Country:N", title="Country"),
            alt.Tooltip("Source:N", title="Source"),
            alt.Tooltip("Value:Q", title="Value", format=".1f"),
        ],
    )
    .properties(
        width=1400,
        height=800,
        title=alt.Title("bar-stacked-percent \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"),
    )
    .configure_axis(grid=True, gridOpacity=0.3)
    .configure_view(strokeWidth=0)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
