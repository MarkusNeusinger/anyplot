""" pyplots.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Simulated country development metrics over years
np.random.seed(42)

# Create 12 countries tracked over 20 years (showing 4 key time points)
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
years = [2000, 2007, 2014, 2021]  # Key time points for faceted view

# Base values for each country (GDP per capita in thousands, life expectancy)
base_gdp = np.array([5, 8, 12, 15, 20, 25, 3, 10, 18, 30, 6, 22])
base_life = np.array([55, 60, 65, 70, 72, 75, 50, 62, 68, 78, 58, 74])
population = np.array([50, 80, 120, 45, 200, 30, 150, 90, 60, 25, 180, 40])  # In millions

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
    for j, year in enumerate(years):
        # Simulate growth over time with some variation
        growth_factor = 1 + j * 0.15 + np.random.uniform(-0.05, 0.1)
        life_improvement = j * 2.5 + np.random.uniform(-1, 2)

        gdp = base_gdp[i] * growth_factor
        life_exp = min(85, base_life[i] + life_improvement)
        pop = population[i] * (1 + j * 0.02)  # Slight population growth

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

# Color palette
color_scale = alt.Scale(domain=["Region 1", "Region 2", "Region 3"], range=["#306998", "#FFD43B", "#6B8E23"])

# Create faceted scatter plot showing evolution across key years
chart = (
    alt.Chart(df)
    .mark_circle(opacity=0.8, stroke="#333333", strokeWidth=1)
    .encode(
        x=alt.X(
            "GDP per Capita (thousands USD):Q", title="GDP per Capita (thousands USD)", scale=alt.Scale(domain=[0, 50])
        ),
        y=alt.Y("Life Expectancy (years):Q", title="Life Expectancy (years)", scale=alt.Scale(domain=[45, 90])),
        size=alt.Size(
            "Population (millions):Q",
            scale=alt.Scale(range=[100, 2000]),
            legend=alt.Legend(title="Population (millions)", titleFontSize=16, labelFontSize=14),
        ),
        color=alt.Color(
            "Region:N", scale=color_scale, legend=alt.Legend(title="Region", titleFontSize=16, labelFontSize=14)
        ),
        tooltip=[
            "Country",
            "Year",
            "GDP per Capita (thousands USD)",
            "Life Expectancy (years)",
            "Population (millions)",
            "Region",
        ],
    )
    .properties(width=350, height=550)
    .facet(
        column=alt.Column(
            "Year:O", header=alt.Header(title=None, labelFontSize=24, labelFontWeight="bold", labelColor="#333333")
        )
    )
    .properties(
        title=alt.Title(
            "scatter-animated-controls · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            subtitle="Country Development Metrics Across Key Years (Static Faceted View)",
            subtitleFontSize=18,
            subtitleColor="#666666",
        )
    )
    .configure_axis(labelFontSize=14, titleFontSize=18, gridColor="#E0E0E0", gridOpacity=0.5)
    .configure_view(strokeWidth=0)
    .configure_legend(orient="right", padding=20)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
