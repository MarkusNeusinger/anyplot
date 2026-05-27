""" anyplot.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: altair 6.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-15
"""

import os
import sys


# Remove current directory from path to prevent import shadowing
cwd = os.getcwd()
sys.path = [p for p in sys.path if os.path.abspath(p) != cwd]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data: Simulated country development metrics over years
np.random.seed(42)

countries = [
    "Country A",
    "Country B",
    "Country C",
    "Country D",
    "Country E",
    "Country F",
    "Country G",
    "Country H",
    "Country I",
    "Country J",
    "Country K",
    "Country L",
]
years_selected = [2000, 2005, 2010, 2015, 2020]

# Base values for each country
base_gdp = np.array([5, 8, 12, 15, 20, 25, 3, 10, 18, 30, 6, 22])
base_life = np.array([55, 60, 65, 70, 72, 75, 50, 62, 68, 78, 58, 74])
population = np.array([50, 80, 120, 45, 200, 30, 150, 90, 60, 25, 180, 40])

# Regions for color coding
regions = [
    "Region 1",
    "Region 2",
    "Region 1",
    "Region 2",
    "Region 3",
    "Region 3",
    "Region 1",
    "Region 2",
    "Region 3",
    "Region 3",
    "Region 1",
    "Region 2",
]

data = []
for i, country in enumerate(countries):
    for year in years_selected:
        years_elapsed = year - 2000
        growth_factor = 1 + years_elapsed * 0.05 + np.random.uniform(-0.03, 0.05)
        life_improvement = years_elapsed * 0.2 + np.random.uniform(-0.5, 0.5)

        gdp = base_gdp[i] * growth_factor
        life_exp = min(85, base_life[i] + life_improvement)
        pop = population[i] * (1 + years_elapsed * 0.015)

        data.append(
            {
                "Country": country,
                "Year": year,
                "GDP per Capita (thousands USD)": round(gdp, 1),
                "Life Expectancy (years)": round(life_exp, 1),
                "Population (millions)": round(pop, 1),
                "Region": regions[i],
            }
        )

df = pd.DataFrame(data)

# Color scale for regions
color_scale = alt.Scale(domain=["Region 1", "Region 2", "Region 3"], range=IMPRINT[:3])

# Create base scatter plot
scatter = (
    alt.Chart(df)
    .mark_circle(opacity=0.7, strokeWidth=1.5)
    .encode(
        x=alt.X(
            "GDP per Capita (thousands USD):Q", title="GDP per Capita (thousands USD)", scale=alt.Scale(domain=[0, 70])
        ),
        y=alt.Y("Life Expectancy (years):Q", title="Life Expectancy (years)", scale=alt.Scale(domain=[45, 90])),
        size=alt.Size(
            "Population (millions):Q",
            scale=alt.Scale(range=[100, 2500]),
            legend=alt.Legend(title="Population", titleFontSize=20, labelFontSize=18),
        ),
        color=alt.Color(
            "Region:N", scale=color_scale, legend=alt.Legend(title="Region", titleFontSize=20, labelFontSize=18)
        ),
        tooltip=[
            alt.Tooltip("Country:N", title="Country"),
            alt.Tooltip("Year:Q", title="Year", format=".0f"),
            alt.Tooltip("GDP per Capita (thousands USD):Q", title="GDP per Capita", format=".1f"),
            alt.Tooltip("Life Expectancy (years):Q", title="Life Expectancy", format=".1f"),
            alt.Tooltip("Population (millions):Q", title="Population", format=".1f"),
            alt.Tooltip("Region:N", title="Region"),
        ],
    )
    .properties(width=280, height=400)
)

# Create faceted chart showing evolution across key years
chart = (
    scatter.facet(
        column=alt.Column(
            "Year:O", header=alt.Header(title=None, labelFontSize=28, labelFontWeight="bold", labelColor=INK)
        )
    )
    .properties(
        title=alt.Title(
            "scatter-animated-controls · altair · anyplot.ai",
            fontSize=32,
            anchor="start",
            subtitle="Country Development Metrics — Evolution Across Key Years",
            subtitleFontSize=22,
        )
    )
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.10,
        labelColor=INK_SOFT,
        labelFontSize=14,
        titleColor=INK,
        titleFontSize=16,
    )
    .configure_title(color=INK, fontSize=32, subtitleColor=INK_SOFT)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        labelFontSize=16,
        titleColor=INK,
        titleFontSize=18,
        padding=15,
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0)
    .properties(background=PAGE_BG)
)

# Save outputs
chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
