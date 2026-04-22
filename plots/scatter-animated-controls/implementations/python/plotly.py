""" pyplots.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
import plotly.express as px


# Data: Simulated country data (GDP, life expectancy, population) over 20 years
np.random.seed(42)

countries = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
regions = ["North", "North", "South", "South", "East", "East", "West", "West"]
years = list(range(2000, 2021))

# Base values for each country
base_gdp = np.array([8000, 12000, 3000, 5000, 15000, 7000, 4000, 20000])
base_life_exp = np.array([65, 72, 58, 62, 75, 68, 60, 78])
base_pop = np.array([50, 30, 120, 80, 25, 45, 90, 20])

# Build dataset with growth trends
data = []
for i, country in enumerate(countries):
    for year_idx, year in enumerate(years):
        # GDP growth with some variation (1-5% annual growth)
        growth_factor = 1 + np.random.uniform(0.01, 0.05)
        gdp = base_gdp[i] * (growth_factor**year_idx) + np.random.normal(0, 500)
        gdp = max(1000, gdp)

        # Life expectancy slowly increases (0.1-0.3 years per year)
        life_exp = base_life_exp[i] + year_idx * np.random.uniform(0.1, 0.3) + np.random.normal(0, 0.5)
        life_exp = min(max(50, life_exp), 85)

        # Population changes (0.5-2% annual change)
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

# Create animated scatter plot with Gapminder-style visualization
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
    color_discrete_sequence=["#306998", "#FFD43B", "#E74C3C", "#2ECC71"],
)

# Update layout for large canvas
fig.update_layout(
    title=dict(
        text="scatter-animated-controls · plotly · pyplots.ai",
        font=dict(size=32, color="#333333"),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="GDP per Capita ($)", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        showgrid=True,
    ),
    yaxis=dict(
        title=dict(text="Life Expectancy (years)", font=dict(size=24)),
        tickfont=dict(size=18),
        gridcolor="rgba(0,0,0,0.1)",
        showgrid=True,
    ),
    legend=dict(
        title=dict(text="Region", font=dict(size=20)),
        font=dict(size=18),
        x=0.02,
        y=0.98,
        bgcolor="rgba(255,255,255,0.8)",
    ),
    template="plotly_white",
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=100, r=100, t=120, b=150),
)

# Update marker styling
fig.update_traces(marker=dict(line=dict(width=2, color="white"), opacity=0.85))

# Update animation settings for smooth playback
fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            showactive=False,
            y=-0.08,
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
            font=dict(size=16),
        )
    ],
    sliders=[
        dict(
            active=0,
            yanchor="top",
            xanchor="left",
            currentvalue=dict(font=dict(size=24), prefix="Year: ", visible=True, xanchor="center"),
            transition=dict(duration=300, easing="cubic-in-out"),
            pad=dict(b=10, t=50),
            len=0.85,
            x=0.1,
            y=-0.02,
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
            font=dict(size=14),
        )
    ],
)

# Add year annotation in background for emphasis
fig.add_annotation(
    x=0.98,
    y=0.95,
    xref="paper",
    yref="paper",
    text="2000",
    showarrow=False,
    font=dict(size=72, color="rgba(0,0,0,0.08)"),
    xanchor="right",
    yanchor="top",
)

# Save static PNG (showing first frame)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
