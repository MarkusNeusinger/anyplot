""" anyplot.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: plotly 6.7.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
import plotly.express as px


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

np.random.seed(42)

countries = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
regions = ["North", "North", "South", "South", "East", "East", "West", "West"]
years = list(range(2000, 2021))

base_gdp = np.array([8000, 12000, 3000, 5000, 15000, 7000, 4000, 20000])
base_life_exp = np.array([65, 72, 58, 62, 75, 68, 60, 78])
base_pop = np.array([50, 30, 120, 80, 25, 45, 90, 20])

data = []
for i, country in enumerate(countries):
    for year_idx, year in enumerate(years):
        growth_factor = 1 + np.random.uniform(0.01, 0.05)
        gdp = base_gdp[i] * (growth_factor**year_idx) + np.random.normal(0, 500)
        gdp = max(1000, gdp)

        life_exp = base_life_exp[i] + year_idx * np.random.uniform(0.1, 0.3) + np.random.normal(0, 0.5)
        life_exp = min(max(50, life_exp), 85)

        pop_factor = 1 + np.random.uniform(0.005, 0.02)
        pop = base_pop[i] * (pop_factor**year_idx) + np.random.normal(0, 2)
        pop = max(10, pop)

        data.append(
            {
                "Country": country,
                "Region": regions[i],
                "Year": year,
                "GDP per Capita ($)": gdp,
                "Life Expectancy (years)": life_exp,
                "Population (millions)": pop,
            }
        )

df = pd.DataFrame(data)

fig = px.scatter(
    df,
    x="GDP per Capita ($)",
    y="Life Expectancy (years)",
    size="Population (millions)",
    color="Region",
    hover_name="Country",
    animation_frame="Year",
    animation_group="Country",
    size_max=80,
    range_x=[0, df["GDP per Capita ($)"].max() * 1.1],
    range_y=[50, 88],
    color_discrete_sequence=IMPRINT,
)

fig.update_layout(
    title=dict(
        text="scatter-animated-controls · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="GDP per Capita ($)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        showgrid=True,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Life Expectancy (years)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        showgrid=True,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    legend=dict(
        title=dict(text="Region", font=dict(size=20, color=INK)),
        font=dict(size=18, color=INK_SOFT),
        x=1.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=100, r=200, t=120, b=150),
)

fig.update_traces(marker=dict(line=dict(width=2, color=PAGE_BG), opacity=0.8))

fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            showactive=False,
            y=-0.12,
            x=0.05,
            xanchor="left",
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
                    args=[
                        None,
                        dict(
                            frame=dict(duration=500, redraw=True),
                            fromcurrent=True,
                            transition=dict(duration=300, easing="cubic-in-out"),
                        ),
                    ],
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[
                        [None],
                        dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0)),
                    ],
                ),
            ],
            font=dict(size=18, color=INK),
            bgcolor=ELEVATED_BG,
            bordercolor=INK_SOFT,
            borderwidth=1,
        )
    ],
    sliders=[
        dict(
            active=0,
            yanchor="top",
            xanchor="left",
            currentvalue=dict(font=dict(size=24, color=INK), prefix="Year: ", visible=True, xanchor="center"),
            transition=dict(duration=300, easing="cubic-in-out"),
            pad=dict(b=10, t=50),
            len=0.85,
            x=0.1,
            y=-0.06,
            steps=[
                dict(
                    args=[
                        [str(year)],
                        dict(frame=dict(duration=300, redraw=True), mode="immediate", transition=dict(duration=300)),
                    ],
                    label=str(year),
                    method="animate",
                )
                for year in years
            ],
            font=dict(size=14, color=INK_SOFT),
        )
    ],
)

fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
