""" pyplots.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
import plotly.express as px


# Data - GDP per capita for European countries (realistic economic indicator)
np.random.seed(42)

# European country ISO codes and approximate GDP per capita (USD)
countries = [
    "DEU",
    "FRA",
    "GBR",
    "ITA",
    "ESP",
    "POL",
    "NLD",
    "BEL",
    "SWE",
    "AUT",
    "CHE",
    "NOR",
    "DNK",
    "FIN",
    "IRL",
    "PRT",
    "GRC",
    "CZE",
    "ROU",
    "HUN",
    "SVK",
    "BGR",
    "HRV",
    "SVN",
    "EST",
    "LVA",
    "LTU",
    "LUX",
    "ISL",
    "SRB",
]

# Realistic GDP per capita values (in thousands USD) - varied distribution
gdp_values = [
    52.0,
    44.0,
    46.0,
    35.0,
    30.0,
    18.0,
    58.0,
    51.0,
    56.0,
    53.0,
    92.0,
    89.0,
    68.0,
    54.0,
    103.0,
    24.0,
    20.0,
    27.0,
    15.0,
    18.0,
    21.0,
    12.0,
    17.0,
    29.0,
    28.0,
    22.0,
    24.0,
    125.0,
    75.0,
    9.0,
]

df = pd.DataFrame({"country": countries, "gdp_per_capita": gdp_values})

# Create choropleth map
fig = px.choropleth(
    df,
    locations="country",
    locationmode="ISO-3",
    color="gdp_per_capita",
    color_continuous_scale="Viridis",
    scope="europe",
    labels={"gdp_per_capita": "GDP per Capita (k USD)"},
)

# Update layout for large canvas
fig.update_layout(
    title={
        "text": "GDP per Capita in Europe · choropleth-basic · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    geo={
        "showframe": False,
        "showcoastlines": True,
        "coastlinecolor": "gray",
        "coastlinewidth": 1,
        "showland": True,
        "landcolor": "lightgray",
        "showocean": True,
        "oceancolor": "aliceblue",
        "showlakes": True,
        "lakecolor": "aliceblue",
        "projection_type": "natural earth",
        "bgcolor": "white",
    },
    coloraxis_colorbar={
        "title": {"text": "GDP per Capita<br>(k USD)", "font": {"size": 20}},
        "tickfont": {"size": 16},
        "len": 0.7,
        "thickness": 25,
        "x": 0.95,
    },
    template="plotly_white",
    margin={"l": 20, "r": 80, "t": 80, "b": 20},
)

# Update traces for better visibility
fig.update_traces(marker_line_color="darkgray", marker_line_width=0.5)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
