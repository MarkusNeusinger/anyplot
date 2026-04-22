""" pyplots.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: altair 6.0.0 | Python 3.13.11
Quality: 93/100 | Created: 2026-01-10
"""

import altair as alt
import pandas as pd


# Data: Major world cities with population (millions)
cities_data = {
    "city": [
        "Tokyo",
        "Delhi",
        "Shanghai",
        "Sao Paulo",
        "Mexico City",
        "Cairo",
        "Mumbai",
        "Beijing",
        "Dhaka",
        "Osaka",
        "New York",
        "Karachi",
        "Buenos Aires",
        "Istanbul",
        "Lagos",
        "Los Angeles",
        "Kolkata",
        "Manila",
        "Rio de Janeiro",
        "Guangzhou",
        "Moscow",
        "Shenzhen",
        "Paris",
        "Jakarta",
        "Lima",
        "Bangkok",
        "London",
        "Chicago",
        "Bogota",
        "Sydney",
    ],
    "latitude": [
        35.68,
        28.61,
        31.23,
        -23.55,
        19.43,
        30.04,
        19.08,
        39.90,
        23.81,
        34.69,
        40.71,
        24.86,
        -34.60,
        41.01,
        6.52,
        34.05,
        22.57,
        14.60,
        -22.91,
        23.13,
        55.76,
        22.54,
        48.86,
        -6.21,
        -12.05,
        13.76,
        51.51,
        41.88,
        4.71,
        -33.87,
    ],
    "longitude": [
        139.69,
        77.21,
        121.47,
        -46.63,
        -99.13,
        31.24,
        72.88,
        116.41,
        90.41,
        135.50,
        -74.01,
        67.01,
        -58.38,
        28.98,
        3.38,
        -118.24,
        88.36,
        120.98,
        -43.17,
        113.26,
        37.62,
        114.06,
        2.35,
        106.85,
        -77.04,
        100.50,
        -0.13,
        -87.63,
        -74.07,
        151.21,
    ],
    "population": [
        37.4,
        32.9,
        29.2,
        22.4,
        21.8,
        21.3,
        21.0,
        20.9,
        22.5,
        19.1,
        18.8,
        16.8,
        15.4,
        15.6,
        15.3,
        12.5,
        15.1,
        14.4,
        13.5,
        14.3,
        12.5,
        13.4,
        11.0,
        11.2,
        11.0,
        10.7,
        9.5,
        8.9,
        11.3,
        5.4,
    ],
    "region": [
        "Asia",
        "Asia",
        "Asia",
        "South America",
        "North America",
        "Africa",
        "Asia",
        "Asia",
        "Asia",
        "Asia",
        "North America",
        "Asia",
        "South America",
        "Europe",
        "Africa",
        "North America",
        "Asia",
        "Asia",
        "South America",
        "Asia",
        "Europe",
        "Asia",
        "Europe",
        "Asia",
        "South America",
        "Asia",
        "Europe",
        "North America",
        "South America",
        "Oceania",
    ],
}

df = pd.DataFrame(cities_data)

# Load world map from vega-datasets URL (works without vega_datasets package)
world_url = "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/world-110m.json"
countries = alt.topo_feature(world_url, "countries")

# Region color mapping (colorblind-safe)
region_colors = {
    "Asia": "#306998",
    "Europe": "#FFD43B",
    "North America": "#2CA02C",
    "South America": "#D62728",
    "Africa": "#9467BD",
    "Oceania": "#17BECF",
}

# Create base map with country boundaries
base_map = (
    alt.Chart(countries)
    .mark_geoshape(fill="#E8E8E0", stroke="#B0B0B0", strokeWidth=0.5)
    .project(type="equirectangular", scale=280, translate=[800, 480])
    .properties(width=1600, height=900)
)

# Create bubble layer with sized markers
bubbles = (
    alt.Chart(df)
    .mark_circle(opacity=0.7, stroke="#FFFFFF", strokeWidth=1.5)
    .encode(
        longitude="longitude:Q",
        latitude="latitude:Q",
        size=alt.Size(
            "population:Q",
            scale=alt.Scale(domain=[5, 40], range=[100, 2500]),
            legend=alt.Legend(
                title="Population (millions)",
                titleFontSize=16,
                labelFontSize=14,
                symbolFillColor="#306998",
                orient="bottom-left",
                offset=20,
            ),
        ),
        color=alt.Color(
            "region:N",
            scale=alt.Scale(domain=list(region_colors.keys()), range=list(region_colors.values())),
            legend=alt.Legend(title="Region", titleFontSize=16, labelFontSize=14, orient="bottom-right", offset=20),
        ),
        tooltip=[
            alt.Tooltip("city:N", title="City"),
            alt.Tooltip("population:Q", title="Population (M)", format=".1f"),
            alt.Tooltip("region:N", title="Region"),
            alt.Tooltip("latitude:Q", title="Latitude", format=".2f"),
            alt.Tooltip("longitude:Q", title="Longitude", format=".2f"),
        ],
    )
    .project(type="equirectangular", scale=280, translate=[800, 480])
)

# Combine base map and bubbles
chart = (
    (base_map + bubbles)
    .properties(
        title=alt.Title(
            text="World City Populations · bubble-map-geographic · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            color="#333333",
        ),
        width=1600,
        height=900,
    )
    .configure_view(stroke=None)
    .configure_legend(titleColor="#333333", labelColor="#555555", padding=15, cornerRadius=5)
)

# Save as PNG (scale 3x for 4800x2700)
chart.save("plot.png", scale_factor=3.0)

# Save interactive HTML version
chart.save("plot.html")
