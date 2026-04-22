""" pyplots.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: altair 6.0.0 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import altair as alt
import numpy as np
import pandas as pd


# Data: Migration flows between major European cities
np.random.seed(42)

cities = {
    "London": (51.5074, -0.1278),
    "Paris": (48.8566, 2.3522),
    "Berlin": (52.5200, 13.4050),
    "Madrid": (40.4168, -3.7038),
    "Rome": (41.9028, 12.4964),
    "Amsterdam": (52.3676, 4.9041),
    "Vienna": (48.2082, 16.3738),
    "Brussels": (50.8503, 4.3517),
    "Lisbon": (38.7223, -9.1393),
    "Dublin": (53.3498, -6.2603),
}

# Create flow data between cities
flows = []
city_names = list(cities.keys())

# Generate flows from major hubs
hub_cities = ["London", "Paris", "Berlin"]
for hub in hub_cities:
    for dest in city_names:
        if hub != dest:
            flow_value = np.random.randint(5000, 50000)
            flows.append(
                {
                    "origin": hub,
                    "origin_lat": cities[hub][0],
                    "origin_lon": cities[hub][1],
                    "dest": dest,
                    "dest_lat": cities[dest][0],
                    "dest_lon": cities[dest][1],
                    "flow": flow_value,
                }
            )

# Add some reverse flows
for origin in ["Madrid", "Rome", "Amsterdam"]:
    for dest in hub_cities:
        flow_value = np.random.randint(2000, 20000)
        flows.append(
            {
                "origin": origin,
                "origin_lat": cities[origin][0],
                "origin_lon": cities[origin][1],
                "dest": dest,
                "dest_lat": cities[dest][0],
                "dest_lon": cities[dest][1],
                "flow": flow_value,
            }
        )

df_flows = pd.DataFrame(flows)

# Create city points data
df_cities = pd.DataFrame([{"city": name, "lat": coords[0], "lon": coords[1]} for name, coords in cities.items()])

# Generate arc paths with control points for curved lines
# For each flow, create intermediate points for Bezier-like curves
arc_data = []
for _, row in df_flows.iterrows():
    # Create multiple points along a curved path
    n_points = 50
    t = np.linspace(0, 1, n_points)

    # Origin and destination
    x0, y0 = row["origin_lon"], row["origin_lat"]
    x1, y1 = row["dest_lon"], row["dest_lat"]

    # Control point offset (perpendicular to line, proportional to distance)
    mid_x = (x0 + x1) / 2
    mid_y = (y0 + y1) / 2
    dx = x1 - x0
    dy = y1 - y0
    dist = np.sqrt(dx**2 + dy**2)

    # Perpendicular offset for curve bulge
    offset = dist * 0.3
    ctrl_x = mid_x - dy / dist * offset
    ctrl_y = mid_y + dx / dist * offset

    # Quadratic Bezier curve
    x_curve = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * ctrl_x + t**2 * x1
    y_curve = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ctrl_y + t**2 * y1

    flow_id = f"{row['origin']}-{row['dest']}"
    for i in range(n_points):
        arc_data.append(
            {
                "flow_id": flow_id,
                "order": i,
                "lon": x_curve[i],
                "lat": y_curve[i],
                "flow": row["flow"],
                "origin": row["origin"],
                "dest": row["dest"],
            }
        )

df_arcs = pd.DataFrame(arc_data)

# Normalize flow for stroke width
max_flow = df_flows["flow"].max()
min_flow = df_flows["flow"].min()
df_arcs["stroke_width"] = 1 + 6 * (df_arcs["flow"] - min_flow) / (max_flow - min_flow)

# Load world basemap from CDN
world_url = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"
world = alt.topo_feature(world_url, "countries")

# Create base map
base = (
    alt.Chart(world)
    .mark_geoshape(fill="#e8e8e8", stroke="white", strokeWidth=0.5)
    .project(type="mercator", scale=800, center=[8, 50], clipExtent=[[0, 0], [1600, 900]])
    .properties(width=1600, height=900)
)

# Create flow arcs layer
arcs = (
    alt.Chart(df_arcs)
    .mark_line(opacity=0.5, strokeCap="round")
    .encode(
        longitude="lon:Q",
        latitude="lat:Q",
        detail="flow_id:N",
        order="order:O",
        strokeWidth=alt.StrokeWidth("stroke_width:Q", scale=None, legend=None),
        color=alt.Color(
            "flow:Q",
            scale=alt.Scale(scheme="blues", domain=[min_flow, max_flow]),
            legend=alt.Legend(
                title="Flow Volume", titleFontSize=18, labelFontSize=14, orient="bottom-right", offset=10
            ),
        ),
        tooltip=["origin:N", "dest:N", "flow:Q"],
    )
    .project(type="mercator", scale=800, center=[8, 50], clipExtent=[[0, 0], [1600, 900]])
)

# Create city points layer
points = (
    alt.Chart(df_cities)
    .mark_circle(size=200, color="#306998", stroke="white", strokeWidth=2)
    .encode(longitude="lon:Q", latitude="lat:Q", tooltip=["city:N"])
    .project(type="mercator", scale=800, center=[8, 50], clipExtent=[[0, 0], [1600, 900]])
)

# Create city labels
labels = (
    alt.Chart(df_cities)
    .mark_text(dy=-15, fontSize=14, fontWeight="bold", color="#333333")
    .encode(longitude="lon:Q", latitude="lat:Q", text="city:N")
    .project(type="mercator", scale=800, center=[8, 50], clipExtent=[[0, 0], [1600, 900]])
)

# Combine layers
chart = (
    (base + arcs + points + labels)
    .properties(
        title=alt.Title("flowmap-origin-destination · altair · pyplots.ai", fontSize=28, anchor="start", offset=20)
    )
    .configure_view(strokeWidth=0)
    .configure_legend(labelFontSize=14, titleFontSize=18)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
