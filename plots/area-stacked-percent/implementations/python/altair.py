""" anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: altair 6.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-12
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Energy source mix evolution
np.random.seed(42)
years = list(range(2015, 2025))

# Evolving percentages showing energy transition (with slight variation for realism)
coal = [45, 42, 39, 35, 32, 28, 25, 22, 19, 16]
natural_gas = [25, 26, 27, 28, 29, 30, 31, 31, 30, 28]
nuclear = [12, 12.5, 12, 11.5, 12, 12.5, 12, 11, 12.5, 12]
renewables = [18, 19.5, 22, 25.5, 27, 29.5, 32, 36, 36.5, 44]

# Create DataFrame in long format for Altair
data = []
for i, year in enumerate(years):
    data.append({"Year": year, "Source": "Renewables", "Percentage": renewables[i]})
    data.append({"Year": year, "Source": "Nuclear", "Percentage": nuclear[i]})
    data.append({"Year": year, "Source": "Natural Gas", "Percentage": natural_gas[i]})
    data.append({"Year": year, "Source": "Coal", "Percentage": coal[i]})

df = pd.DataFrame(data)

# Define stacking order (bottom to top)
source_order = ["Coal", "Natural Gas", "Nuclear", "Renewables"]
stack_order = {"Coal": 1, "Natural Gas": 2, "Nuclear": 3, "Renewables": 4}
df["StackOrder"] = df["Source"].map(stack_order)

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
            scale=alt.Scale(domain=source_order, range=IMPRINT),
            legend=alt.Legend(
                title="Energy Source",
                titleFontSize=20,
                labelFontSize=18,
                orient="bottom",
                direction="horizontal",
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
        width=1600,
        height=900,
        title=alt.Title(text="area-stacked-percent · altair · anyplot.ai", fontSize=28),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT)
    .configure_axis(
        domainColor=INK_SOFT, tickColor=INK_SOFT, gridColor=INK, gridOpacity=0.10, labelColor=INK_SOFT, titleColor=INK
    )
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
