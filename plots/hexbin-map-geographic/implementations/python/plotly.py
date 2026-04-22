""" pyplots.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import h3
import numpy as np
import pandas as pd
import plotly.express as px


# Data: Simulate taxi pickup locations in NYC area with fare values
np.random.seed(42)
n_points = 5000
lat_center, lon_center = 40.7580, -73.9855

# Generate clustered pickup locations using vectorized operations
cluster_centers_lat = lat_center + np.random.uniform(-0.08, 0.08, 8)
cluster_centers_lon = lon_center + np.random.uniform(-0.10, 0.10, 8)
cluster_assignments = np.random.choice(8, n_points, p=np.random.dirichlet(np.ones(8)))

lats = cluster_centers_lat[cluster_assignments] + np.random.normal(0, 0.015, n_points)
lons = cluster_centers_lon[cluster_assignments] + np.random.normal(0, 0.02, n_points)
fares = np.random.exponential(15, n_points) + 5

df = pd.DataFrame({"lat": lats, "lon": lons, "fare": fares})

# Convert lat/lon to H3 hexagonal cells (resolution 9 ~ 0.1 km² cells)
df["h3_cell"] = [h3.latlng_to_cell(lat, lon, 9) for lat, lon in zip(df["lat"], df["lon"], strict=True)]

# Aggregate by hexagonal cell: count, sum, and mean (demonstrating all three methods)
hex_agg = (
    df.groupby("h3_cell")
    .agg(count=("fare", "size"), total_fare=("fare", "sum"), mean_fare=("fare", "mean"))
    .reset_index()
)

# Build GeoJSON using list comprehension for cleaner structure
geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": row["h3_cell"],
            "properties": {
                "count": int(row["count"]),
                "mean_fare": round(row["mean_fare"], 2),
                "total_fare": round(row["total_fare"], 2),
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[c[1], c[0]] for c in h3.cell_to_boundary(row["h3_cell"])]
                    + [[h3.cell_to_boundary(row["h3_cell"])[0][1], h3.cell_to_boundary(row["h3_cell"])[0][0]]]
                ],
            },
        }
        for _, row in hex_agg.iterrows()
    ],
}

# Create choropleth map colored by mean fare (demonstrating mean aggregation)
fig = px.choropleth_map(
    hex_agg,
    geojson=geojson,
    locations="h3_cell",
    color="mean_fare",
    color_continuous_scale="YlOrRd",
    opacity=0.75,
    center={"lat": lat_center, "lon": lon_center},
    zoom=11,
    map_style="carto-positron",
    hover_data={"h3_cell": False, "count": ":,", "mean_fare": ":$.2f", "total_fare": ":$,.0f"},
)

# Update layout with clear labeling
fig.update_layout(
    title={
        "text": "NYC Taxi Fares · hexbin-map-geographic · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    coloraxis_colorbar={
        "title": {"text": "Avg Fare ($)", "font": {"size": 20}},
        "tickfont": {"size": 16},
        "tickprefix": "$",
        "len": 0.7,
        "thickness": 25,
    },
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
)

# Make hexagon boundaries clearly visible with contrasting dark lines
fig.update_traces(marker_line_width=2, marker_line_color="rgba(30, 30, 30, 0.8)")

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
