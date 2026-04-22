""" pyplots.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - European cities with population-like density values
np.random.seed(42)

# Generate synthetic data points around major European city centers
cities = [
    # (name, lat, lon, spread, n_points, weight_base)
    ("London", 51.5, -0.1, 0.8, 80, 1.5),
    ("Paris", 48.9, 2.3, 0.6, 70, 1.4),
    ("Berlin", 52.5, 13.4, 0.7, 55, 1.2),
    ("Madrid", 40.4, -3.7, 0.5, 50, 1.1),
    ("Rome", 41.9, 12.5, 0.4, 45, 1.0),
    ("Vienna", 48.2, 16.4, 0.4, 35, 0.9),
    ("Amsterdam", 52.4, 4.9, 0.3, 40, 1.0),
    ("Brussels", 50.8, 4.4, 0.3, 35, 0.9),
    ("Warsaw", 52.2, 21.0, 0.5, 40, 0.8),
    ("Prague", 50.1, 14.4, 0.3, 30, 0.8),
    ("Stockholm", 59.3, 18.1, 0.4, 30, 0.7),
    ("Munich", 48.1, 11.6, 0.3, 35, 0.9),
    ("Milan", 45.5, 9.2, 0.4, 40, 1.0),
    ("Barcelona", 41.4, 2.2, 0.4, 45, 1.0),
    ("Lisbon", 38.7, -9.1, 0.4, 30, 0.8),
]

data_rows = []
for _name, lat, lon, spread, n, weight in cities:
    lats = np.random.normal(lat, spread, n)
    lons = np.random.normal(lon, spread * 1.2, n)
    values = np.random.exponential(weight, n) * 10
    for i in range(n):
        data_rows.append({"latitude": lats[i], "longitude": lons[i], "value": values[i]})

# Add some scattered rural points
n_rural = 200
rural_lats = np.random.uniform(36, 62, n_rural)
rural_lons = np.random.uniform(-10, 25, n_rural)
rural_values = np.random.exponential(0.3, n_rural) * 5
for i in range(n_rural):
    data_rows.append({"latitude": rural_lats[i], "longitude": rural_lons[i], "value": rural_values[i]})

df = pd.DataFrame(data_rows)

# Load world countries from natural earth (Vega datasets URL)
countries_url = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"
countries = alt.topo_feature(countries_url, "countries")

# Basemap layer - country boundaries
basemap = (
    alt.Chart(countries)
    .mark_geoshape(fill="#e8e8e8", stroke="#999999", strokeWidth=0.8)
    .project(type="mercator", scale=600, center=[10, 50])
)

# Create a heatmap effect using overlapping circles with color encoding
# The circles have transparency to create the heatmap blending effect
heatmap_points = (
    alt.Chart(df)
    .mark_circle(opacity=0.5)
    .encode(
        longitude="longitude:Q",
        latitude="latitude:Q",
        size=alt.Size("value:Q", scale=alt.Scale(range=[100, 1500]), legend=None),
        color=alt.Color(
            "value:Q",
            scale=alt.Scale(scheme="inferno", domain=[0, 30]),
            legend=alt.Legend(
                title="Intensity",
                titleFontSize=18,
                labelFontSize=14,
                gradientLength=300,
                gradientThickness=20,
                orient="right",
            ),
        ),
        tooltip=[
            alt.Tooltip("latitude:Q", format=".2f", title="Lat"),
            alt.Tooltip("longitude:Q", format=".2f", title="Lon"),
            alt.Tooltip("value:Q", format=".1f", title="Value"),
        ],
    )
    .project(type="mercator", scale=600, center=[10, 50])
)

# Combine layers
chart = (
    alt.layer(basemap, heatmap_points)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "European Activity Density · heatmap-geographic · altair · pyplots.ai", fontSize=28, anchor="middle"
        ),
    )
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=18, labelFontSize=14)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
