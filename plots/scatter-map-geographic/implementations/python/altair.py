""" pyplots.ai
scatter-map-geographic: Scatter Map with Geographic Points
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-10
"""

import altair as alt
import pandas as pd


# Data: Major world cities with population and region
cities_data = {
    "city": [
        "Tokyo",
        "Delhi",
        "Shanghai",
        "São Paulo",
        "Mexico City",
        "Cairo",
        "Mumbai",
        "Beijing",
        "Dhaka",
        "Osaka",
        "New York",
        "Karachi",
        "Buenos Aires",
        "Chongqing",
        "Istanbul",
        "Kolkata",
        "Manila",
        "Lagos",
        "Rio de Janeiro",
        "Tianjin",
        "Kinshasa",
        "Guangzhou",
        "Los Angeles",
        "Moscow",
        "Shenzhen",
        "Lahore",
        "Bangalore",
        "Paris",
        "Bogotá",
        "Jakarta",
        "Lima",
        "Bangkok",
        "London",
        "Chennai",
        "Hyderabad",
        "Nagoya",
        "Ho Chi Minh City",
        "Johannesburg",
        "Toronto",
        "Sydney",
    ],
    "latitude": [
        35.6762,
        28.7041,
        31.2304,
        -23.5505,
        19.4326,
        30.0444,
        19.0760,
        39.9042,
        23.8103,
        34.6937,
        40.7128,
        24.8607,
        -34.6037,
        29.4316,
        41.0082,
        22.5726,
        14.5995,
        6.5244,
        -22.9068,
        39.3434,
        -4.4419,
        23.1291,
        34.0522,
        55.7558,
        22.5431,
        31.5497,
        12.9716,
        48.8566,
        4.7110,
        -6.2088,
        -12.0464,
        13.7563,
        51.5074,
        13.0827,
        17.3850,
        35.1815,
        10.8231,
        -26.2041,
        43.6532,
        -33.8688,
    ],
    "longitude": [
        139.6503,
        77.1025,
        121.4737,
        -46.6333,
        -99.1332,
        31.2357,
        72.8777,
        116.4074,
        90.4125,
        135.5023,
        -74.0060,
        67.0011,
        -58.3816,
        106.9123,
        28.9784,
        88.3639,
        120.9842,
        3.3792,
        -43.1729,
        117.3616,
        15.2663,
        113.2644,
        -118.2437,
        37.6173,
        114.0579,
        74.3436,
        77.5946,
        2.3522,
        -74.0721,
        106.8456,
        -77.0428,
        100.5018,
        -0.1278,
        80.2707,
        78.4867,
        136.9066,
        106.6297,
        28.0473,
        -79.3832,
        151.2093,
    ],
    "population_millions": [
        37.4,
        32.9,
        29.2,
        22.4,
        21.9,
        21.3,
        21.0,
        20.9,
        20.3,
        19.2,
        18.8,
        16.5,
        15.4,
        15.4,
        15.2,
        14.9,
        14.2,
        14.1,
        13.6,
        13.6,
        13.2,
        13.0,
        12.5,
        12.5,
        12.4,
        12.3,
        12.2,
        11.0,
        10.9,
        10.8,
        10.7,
        10.5,
        9.5,
        9.3,
        9.2,
        9.1,
        8.8,
        5.8,
        6.2,
        5.3,
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
        "Asia",
        "Europe",
        "Asia",
        "Asia",
        "Africa",
        "South America",
        "Asia",
        "Africa",
        "Asia",
        "North America",
        "Europe",
        "Asia",
        "Asia",
        "Asia",
        "Europe",
        "South America",
        "Asia",
        "South America",
        "Asia",
        "Europe",
        "Asia",
        "Asia",
        "Asia",
        "Asia",
        "Africa",
        "North America",
        "Oceania",
    ],
}

df = pd.DataFrame(cities_data)

# Load world basemap from world-atlas
world = alt.topo_feature("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json", "countries")

# Create basemap layer
basemap = (
    alt.Chart(world)
    .mark_geoshape(fill="#e8e8e8", stroke="#ffffff", strokeWidth=0.5)
    .project(type="naturalEarth1")
    .properties(width=1600, height=900)
)

# Define color scale for regions
region_colors = ["#306998", "#FFD43B", "#E74C3C", "#2ECC71", "#9B59B6", "#1ABC9C"]

# Create scatter points layer
points = (
    alt.Chart(df)
    .mark_circle(opacity=0.8, stroke="#ffffff", strokeWidth=1)
    .encode(
        longitude="longitude:Q",
        latitude="latitude:Q",
        size=alt.Size(
            "population_millions:Q",
            scale=alt.Scale(range=[100, 2000]),
            legend=alt.Legend(
                title="Population (millions)", titleFontSize=18, labelFontSize=16, orient="bottom-left", offset=20
            ),
        ),
        color=alt.Color(
            "region:N",
            scale=alt.Scale(range=region_colors),
            legend=alt.Legend(title="Region", titleFontSize=18, labelFontSize=16, orient="bottom-right", offset=20),
        ),
        tooltip=["city:N", "population_millions:Q", "region:N"],
    )
    .project(type="naturalEarth1")
    .properties(width=1600, height=900)
)

# Combine layers
chart = (
    alt.layer(basemap, points)
    .properties(
        title=alt.Title(
            text="World Major Cities · scatter-map-geographic · altair · pyplots.ai",
            fontSize=28,
            anchor="middle",
            color="#333333",
        )
    )
    .configure_view(stroke=None)
    .configure_legend(padding=15, cornerRadius=5, fillColor="#ffffff", strokeColor="#cccccc")
)

# Save as PNG and HTML
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
