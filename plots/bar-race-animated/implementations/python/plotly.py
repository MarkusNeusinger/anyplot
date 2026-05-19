"""anyplot.ai
bar-race-animated: Animated Bar Chart Race
Library: plotly | Python 3.13
Quality: pending | Created: 2026-05-19
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.25)" if THEME == "light" else "rgba(240,239,232,0.25)"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data: Major economy GDP rankings (approximate, in trillion USD, 1995–2023)
np.random.seed(42)

countries = ["USA", "China", "Japan", "Germany", "UK", "France", "Brazil"]
years = list(range(1995, 2024))

base_gdp = {"USA": 7.70, "China": 0.73, "Japan": 5.45, "Germany": 2.60, "UK": 1.28, "France": 1.60, "Brazil": 0.77}
color_map = dict(zip(countries, OKABE_ITO))

data_rows = []
for country in countries:
    gdp = base_gdp[country]
    for year in years:
        noise = np.random.uniform(0.99, 1.01)
        data_rows.append({"Country": country, "Year": year, "GDP": round(gdp * noise, 3)})
        if country == "USA":
            rate = -0.020 if year == 2009 else 0.047
        elif country == "China":
            rate = 0.115 if year < 2005 else (0.138 if year < 2015 else (0.072 if year < 2020 else 0.056))
        elif country == "Japan":
            rate = -0.012 if year in [2009, 2011] else 0.014
        elif country == "Germany":
            rate = -0.050 if year == 2009 else 0.040
        elif country == "UK":
            rate = -0.040 if year == 2009 else 0.042
        elif country == "France":
            rate = -0.030 if year == 2009 else 0.037
        else:  # Brazil
            rate = 0.083 if year < 2011 else (0.025 if year < 2015 else (-0.005 if year < 2019 else 0.038))
        gdp = gdp * (1 + rate)

df = pd.DataFrame(data_rows)
max_gdp = df["GDP"].max() * 1.18
title_text = "GDP Rankings · bar-race-animated · python · plotly · anyplot.ai"

shared_xaxis = dict(
    title=dict(text="GDP (Trillion USD)", font=dict(size=22, color=INK)),
    tickfont=dict(size=18, color=INK_SOFT),
    range=[0, max_gdp],
    gridcolor=GRID,
    linecolor=INK_SOFT,
    zerolinecolor=INK_SOFT,
)
shared_yaxis = dict(tickfont=dict(size=20, color=INK_SOFT), linecolor=INK_SOFT, showgrid=False)
shared_margin = dict(l=150, r=160, t=140, b=160)

# Animation frames: bars sorted by GDP value each year
frames = []
slider_steps = []
for year in years:
    year_data = df[df["Year"] == year].sort_values("GDP", ascending=True)
    frames.append(
        go.Frame(
            data=[
                go.Bar(
                    x=year_data["GDP"],
                    y=year_data["Country"],
                    orientation="h",
                    text=[f"{v:.1f}T" for v in year_data["GDP"]],
                    textposition="outside",
                    textfont=dict(size=18, color=INK),
                    marker=dict(color=[color_map[c] for c in year_data["Country"]], line=dict(width=0)),
                )
            ],
            name=str(year),
        )
    )
    slider_steps.append(
        dict(
            args=[
                [str(year)],
                dict(frame=dict(duration=600, redraw=True), mode="immediate", transition=dict(duration=300)),
            ],
            label=str(year),
            method="animate",
        )
    )

# Initial state: 1995
init_data = df[df["Year"] == years[0]].sort_values("GDP", ascending=True)

fig_anim = go.Figure(
    data=[
        go.Bar(
            x=init_data["GDP"],
            y=init_data["Country"],
            orientation="h",
            text=[f"{v:.1f}T" for v in init_data["GDP"]],
            textposition="outside",
            textfont=dict(size=18, color=INK),
            marker=dict(color=[color_map[c] for c in init_data["Country"]], line=dict(width=0)),
        )
    ],
    layout=go.Layout(
        title=dict(text=title_text, font=dict(size=28, color=INK), x=0.5, xanchor="center"),
        xaxis=shared_xaxis,
        yaxis=shared_yaxis,
        paper_bgcolor=PAGE_BG,
        plot_bgcolor=PAGE_BG,
        margin=shared_margin,
        showlegend=False,
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                y=1.08,
                x=0.0,
                xanchor="left",
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=600, redraw=True), fromcurrent=True, transition=dict(duration=300)
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
            )
        ],
        sliders=[
            dict(
                active=0,
                currentvalue=dict(font=dict(size=24, color=INK), prefix="Year: ", visible=True, xanchor="center"),
                font=dict(size=16, color=INK_SOFT),
                bgcolor=ELEVATED_BG,
                bordercolor=INK_SOFT,
                steps=slider_steps,
                pad=dict(b=10, t=50),
            )
        ],
    ),
    frames=frames,
)

fig_anim.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

# Static PNG: final year (2023) snapshot showing the race outcome
final_data = df[df["Year"] == years[-1]].sort_values("GDP", ascending=True)

fig_png = go.Figure(
    data=[
        go.Bar(
            x=final_data["GDP"],
            y=final_data["Country"],
            orientation="h",
            text=[f"{v:.1f}T" for v in final_data["GDP"]],
            textposition="outside",
            textfont=dict(size=18, color=INK),
            marker=dict(color=[color_map[c] for c in final_data["Country"]], line=dict(width=0)),
        )
    ]
)
fig_png.update_layout(
    title=dict(text=title_text, font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="GDP (Trillion USD) — 2023 snapshot", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        range=[0, max_gdp],
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=shared_yaxis,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin=dict(l=150, r=160, t=120, b=100),
    showlegend=False,
)

fig_png.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
