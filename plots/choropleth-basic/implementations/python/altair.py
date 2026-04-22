""" pyplots.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
from vega_datasets import data


# Data - US unemployment rate by county
counties = alt.topo_feature(data.us_10m.url, "counties")
unemployment = data.unemployment()

# Create choropleth map
chart = (
    alt.Chart(counties)
    .mark_geoshape(stroke="white", strokeWidth=0.3)
    .encode(
        color=alt.Color(
            "rate:Q",
            scale=alt.Scale(scheme="blues", domain=[0, 0.25]),
            legend=alt.Legend(
                title="Unemployment (%)",
                titleFontSize=20,
                labelFontSize=16,
                gradientLength=400,
                gradientThickness=25,
                titleLimit=200,
            ),
        ),
        tooltip=[
            alt.Tooltip("id:O", title="County ID"),
            alt.Tooltip("rate:Q", title="Unemployment Rate (%)", format=".1%"),
        ],
    )
    .transform_lookup(lookup="id", from_=alt.LookupData(unemployment, "id", ["rate"]))
    .project(type="albersUsa")
    .properties(
        width=1500,
        height=950,
        title=alt.Title(
            text="US County Unemployment · choropleth-basic · altair · pyplots.ai", fontSize=28, anchor="middle"
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(orient="right", offset=30, padding=10)
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
