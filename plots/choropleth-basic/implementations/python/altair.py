"""anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: altair | Python 3.13
Quality: pending | Created: 2025-12-31
"""

import os

import altair as alt
from vega_datasets import data


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - US unemployment rate by county
counties = alt.topo_feature(data.us_10m.url, "counties")
unemployment = data.unemployment()

# Create choropleth map
chart = (
    alt.Chart(counties)
    .mark_geoshape(stroke=INK_SOFT, strokeWidth=0.5)
    .encode(
        color=alt.Color(
            "rate:Q",
            scale=alt.Scale(scheme="blues", domain=[0, 0.25]),
            legend=alt.Legend(
                title="Unemployment Rate",
                titleFontSize=20,
                labelFontSize=16,
                gradientLength=400,
                gradientThickness=25,
                titleLimit=200,
                format=".0%",
            ),
        ),
        tooltip=[
            alt.Tooltip("id:O", title="County ID"),
            alt.Tooltip("rate:Q", title="Unemployment Rate", format=".1%"),
        ],
    )
    .transform_lookup(lookup="id", from_=alt.LookupData(unemployment, "id", ["rate"]))
    .project(type="albersUsa")
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            text="US County Unemployment · choropleth-basic · altair · anyplot.ai", fontSize=28, anchor="middle"
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK_SOFT,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        titleColor=INK,
    )
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        orient="right",
        offset=30,
        padding=10,
    )
    .interactive()
)

# Save as PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
