""" pyplots.ai
map-marker-clustered: Clustered Marker Map
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import altair as alt
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering


# Data - Generate store locations across the United States
np.random.seed(42)

# Major city centers (lat, lon) with category weights
cities = [
    (40.7128, -74.0060, "New York", "retail"),
    (34.0522, -118.2437, "Los Angeles", "retail"),
    (41.8781, -87.6298, "Chicago", "food"),
    (29.7604, -95.3698, "Houston", "food"),
    (33.4484, -112.0740, "Phoenix", "services"),
    (39.7392, -104.9903, "Denver", "services"),
    (47.6062, -122.3321, "Seattle", "retail"),
    (25.7617, -80.1918, "Miami", "food"),
    (42.3601, -71.0589, "Boston", "retail"),
    (38.9072, -77.0369, "Washington DC", "services"),
]

categories = ["retail", "food", "services"]
n_points = 500

# Generate points clustered around cities
lats = []
lons = []
labels = []
cats = []

for i in range(n_points):
    city = cities[i % len(cities)]
    lat_offset = np.random.normal(0, 1.5)
    lon_offset = np.random.normal(0, 1.5)
    lats.append(city[0] + lat_offset)
    lons.append(city[1] + lon_offset)
    labels.append(f"Store {i + 1}")
    cats.append(city[3])

df = pd.DataFrame({"lat": lats, "lon": lons, "label": labels, "category": cats})

# Pre-compute clusters for static visualization
# Use hierarchical clustering with distance threshold
coords = df[["lat", "lon"]].values
clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=2.0, linkage="average")
cluster_labels = clustering.fit_predict(coords)
df["cluster"] = cluster_labels

# Create cluster summary
cluster_summary = (
    df.groupby("cluster")
    .agg(
        lat=("lat", "mean"),
        lon=("lon", "mean"),
        count=("label", "count"),
        dominant_category=("category", lambda x: x.mode().iloc[0]),
    )
    .reset_index()
)

# Determine marker size based on count (log scale for visual clarity)
cluster_summary["size"] = np.log1p(cluster_summary["count"]) * 150 + 100

# Load US states background from official Vega datasets URL
us_10m_url = "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/us-10m.json"
states = alt.topo_feature(us_10m_url, "states")

# Background map layer
background = (
    alt.Chart(states)
    .mark_geoshape(fill="#f0f0f0", stroke="#cccccc", strokeWidth=0.5)
    .project(type="albersUsa")
    .properties(width=1600, height=900)
)

# Color scheme for categories (Python colors first)
category_colors = alt.Scale(domain=["retail", "food", "services"], range=["#306998", "#FFD43B", "#4B8BBE"])

# Cluster markers layer
clusters = (
    alt.Chart(cluster_summary)
    .mark_circle(opacity=0.8, stroke="#ffffff", strokeWidth=2)
    .encode(
        longitude="lon:Q",
        latitude="lat:Q",
        size=alt.Size("size:Q", scale=alt.Scale(range=[200, 2000]), legend=None),
        color=alt.Color("dominant_category:N", scale=category_colors, title="Category"),
        tooltip=[
            alt.Tooltip("count:Q", title="Locations"),
            alt.Tooltip("dominant_category:N", title="Primary Type"),
            alt.Tooltip("lat:Q", title="Latitude", format=".2f"),
            alt.Tooltip("lon:Q", title="Longitude", format=".2f"),
        ],
    )
    .project(type="albersUsa")
)

# Cluster count labels
labels_layer = (
    alt.Chart(cluster_summary[cluster_summary["count"] > 1])
    .mark_text(fontSize=14, fontWeight="bold", color="#ffffff")
    .encode(longitude="lon:Q", latitude="lat:Q", text="count:Q")
    .project(type="albersUsa")
)

# Combine layers
chart = (
    (background + clusters + labels_layer)
    .properties(
        title=alt.Title(
            text="map-marker-clustered · altair · pyplots.ai",
            subtitle="500 store locations clustered by proximity (cluster size indicates count)",
            fontSize=28,
            subtitleFontSize=18,
            anchor="start",
        )
    )
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=18, labelFontSize=16, symbolSize=300, orient="bottom-right")
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
