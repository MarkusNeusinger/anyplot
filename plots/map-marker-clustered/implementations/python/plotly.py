""" pyplots.ai
map-marker-clustered: Clustered Marker Map
Library: plotly 6.5.2 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data - Simulating retail store locations across North America
np.random.seed(42)

# Generate clustered store locations in major cities
cities = {
    "New York": (40.7128, -74.0060, 80),
    "Los Angeles": (34.0522, -118.2437, 60),
    "Chicago": (41.8781, -87.6298, 50),
    "Houston": (29.7604, -95.3698, 40),
    "Phoenix": (33.4484, -112.0740, 35),
    "Seattle": (47.6062, -122.3321, 30),
    "Denver": (39.7392, -104.9903, 25),
    "Miami": (25.7617, -80.1918, 45),
    "Atlanta": (33.7490, -84.3880, 35),
    "Boston": (42.3601, -71.0589, 40),
}

categories = ["Electronics", "Grocery", "Clothing", "Hardware"]
category_colors = {"Electronics": "#306998", "Grocery": "#2ecc71", "Clothing": "#e74c3c", "Hardware": "#FFD43B"}

lats, lons, labels, cats = [], [], [], []
store_id = 1

for city, (lat, lon, count) in cities.items():
    for _ in range(count):
        # Add jitter around city center
        lat_jitter = lat + np.random.normal(0, 0.15)
        lon_jitter = lon + np.random.normal(0, 0.15)
        category = np.random.choice(categories)
        lats.append(lat_jitter)
        lons.append(lon_jitter)
        labels.append(f"Store #{store_id} - {city}")
        cats.append(category)
        store_id += 1

df = pd.DataFrame({"lat": lats, "lon": lons, "label": labels, "category": cats})

# Create figure with Scattermap for geographic plotting (uses MapLibre)
fig = go.Figure()

# Add traces for each category with clustering enabled
for category in categories:
    cat_df = df[df["category"] == category]
    fig.add_trace(
        go.Scattermap(
            lat=cat_df["lat"],
            lon=cat_df["lon"],
            mode="markers",
            marker={"size": 14, "color": category_colors[category], "opacity": 0.8},
            text=cat_df["label"],
            hovertemplate="<b>%{text}</b><br>Category: "
            + category
            + "<br>Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<extra></extra>",
            name=category,
            cluster={
                "enabled": True,
                "maxzoom": 10,
                "size": 40,
                "step": 1,
                "color": category_colors[category],
                "opacity": 0.9,
            },
        )
    )

# Update layout with map styling
fig.update_layout(
    title={
        "text": "Retail Store Locations (440 stores) · map-marker-clustered · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333"},
        "x": 0.5,
        "xanchor": "center",
    },
    map={
        "style": "carto-positron",
        "center": {"lat": 39.0, "lon": -98.0},  # Center of US
        "zoom": 3.5,
    },
    legend={
        "title": {"text": "Store Category", "font": {"size": 18}},
        "font": {"size": 16},
        "bgcolor": "rgba(255, 255, 255, 0.9)",
        "bordercolor": "#ccc",
        "borderwidth": 1,
        "x": 0.01,
        "y": 0.99,
        "xanchor": "left",
        "yanchor": "top",
    },
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
    template="plotly_white",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
