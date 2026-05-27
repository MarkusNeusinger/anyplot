""" anyplot.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-08
"""

import os

import altair as alt
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Energy mix by country
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
            title="Share of Energy Mix (%)",
        ),
        color=alt.Color(
            "Source:N",
            scale=alt.Scale(domain=["Fossil Fuels", "Nuclear", "Renewables", "Hydro"], range=IMPRINT),
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
        width=1600,
        height=900,
        background=PAGE_BG,
        title=alt.Title("bar-stacked-percent · altair · anyplot.ai", fontSize=28, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.15, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save PNG and HTML
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
