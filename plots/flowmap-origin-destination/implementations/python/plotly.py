""" pyplots.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import numpy as np
import plotly.graph_objects as go


# Data: Major international trade flows (synthetic example)
np.random.seed(42)

# Define major cities with coordinates (origin-destination pairs)
cities = {
    "Shanghai": (31.2, 121.5),
    "Los Angeles": (34.1, -118.2),
    "Rotterdam": (51.9, 4.5),
    "Singapore": (1.3, 103.8),
    "Dubai": (25.3, 55.3),
    "New York": (40.7, -74.0),
    "Tokyo": (35.7, 139.7),
    "Hamburg": (53.6, 10.0),
    "Busan": (35.2, 129.1),
    "Hong Kong": (22.3, 114.2),
    "Santos": (-23.9, -46.3),
    "Mumbai": (19.1, 72.9),
    "Sydney": (-33.9, 151.2),
    "Cape Town": (-33.9, 18.4),
    "Panama City": (9.0, -79.5),
}

# Define trade flows (origin, destination, volume in millions of tons)
flows_data = [
    ("Shanghai", "Los Angeles", 85),
    ("Shanghai", "Rotterdam", 72),
    ("Singapore", "Rotterdam", 68),
    ("Shanghai", "New York", 58),
    ("Hong Kong", "Los Angeles", 52),
    ("Tokyo", "Shanghai", 48),
    ("Rotterdam", "New York", 45),
    ("Dubai", "Rotterdam", 42),
    ("Busan", "Los Angeles", 40),
    ("Shanghai", "Hamburg", 38),
    ("Mumbai", "Singapore", 35),
    ("Shanghai", "Sydney", 32),
    ("Hong Kong", "Dubai", 30),
    ("Santos", "Rotterdam", 28),
    ("Cape Town", "Singapore", 25),
    ("Shanghai", "Dubai", 45),
    ("Singapore", "Hong Kong", 55),
    ("Los Angeles", "Panama City", 22),
    ("Rotterdam", "Mumbai", 20),
    ("Tokyo", "Los Angeles", 36),
    ("Sydney", "Singapore", 18),
    ("Hamburg", "New York", 24),
    ("Dubai", "Mumbai", 33),
    ("Busan", "Shanghai", 29),
    ("Hong Kong", "Hamburg", 26),
]

# Prepare data for plotting
origin_names = [f[0] for f in flows_data]
dest_names = [f[1] for f in flows_data]
origin_lats = [cities[f[0]][0] for f in flows_data]
origin_lons = [cities[f[0]][1] for f in flows_data]
dest_lats = [cities[f[1]][0] for f in flows_data]
dest_lons = [cities[f[1]][1] for f in flows_data]
flow_values = [f[2] for f in flows_data]

# Normalize flow values for line width (2-10 range)
max_flow = max(flow_values)
min_flow = min(flow_values)
line_widths = [2 + 8 * (f - min_flow) / (max_flow - min_flow) for f in flow_values]

# Create figure
fig = go.Figure()

# Add flow arcs as curved lines
for i in range(len(flows_data)):
    o_lat, o_lon = origin_lats[i], origin_lons[i]
    d_lat, d_lon = dest_lats[i], dest_lons[i]

    # Create Bezier curve points for arc
    t = np.linspace(0, 1, 50)
    mid_lat = (o_lat + d_lat) / 2
    mid_lon = (o_lon + d_lon) / 2

    # Calculate arc height based on distance
    dist = np.sqrt((d_lat - o_lat) ** 2 + (d_lon - o_lon) ** 2)
    arc_height = dist * 0.2

    # Perpendicular offset for control point
    dx = d_lon - o_lon
    dy = d_lat - o_lat
    perp_x = -dy / (dist + 0.001) * arc_height * 2
    perp_y = dx / (dist + 0.001) * arc_height * 2

    ctrl_lat = mid_lat + perp_y
    ctrl_lon = mid_lon + perp_x

    # Quadratic Bezier curve
    arc_lats = (1 - t) ** 2 * o_lat + 2 * (1 - t) * t * ctrl_lat + t**2 * d_lat
    arc_lons = (1 - t) ** 2 * o_lon + 2 * (1 - t) * t * ctrl_lon + t**2 * d_lon

    # Color based on flow magnitude (blue gradient)
    intensity = (flow_values[i] - min_flow) / (max_flow - min_flow)
    r = int(30 + 20 * (1 - intensity))
    g = int(105 - 60 * intensity)
    b = int(152 + 50 * intensity)
    color = f"rgba({r}, {g}, {b}, 0.6)"

    fig.add_trace(
        go.Scattergeo(
            lon=arc_lons,
            lat=arc_lats,
            mode="lines",
            line={"width": line_widths[i], "color": color},
            hoverinfo="text",
            hovertext=f"{origin_names[i]} → {dest_names[i]}<br>Volume: {flow_values[i]}M tons",
            showlegend=False,
        )
    )

# Add city markers (origins and destinations)
all_cities_set = set(origin_names) | set(dest_names)
city_lats = [cities[c][0] for c in all_cities_set]
city_lons = [cities[c][1] for c in all_cities_set]
city_labels = list(all_cities_set)

# Calculate marker sizes based on total flow through each city
city_flow_totals = {}
for o, d, v in flows_data:
    city_flow_totals[o] = city_flow_totals.get(o, 0) + v
    city_flow_totals[d] = city_flow_totals.get(d, 0) + v

marker_sizes = [10 + 15 * city_flow_totals[c] / max(city_flow_totals.values()) for c in city_labels]

fig.add_trace(
    go.Scattergeo(
        lon=city_lons,
        lat=city_lats,
        mode="markers+text",
        marker={"size": marker_sizes, "color": "#306998", "line": {"width": 2, "color": "white"}},
        text=city_labels,
        textposition="top center",
        textfont={"size": 14, "color": "#333333"},
        hoverinfo="text",
        hovertext=[f"{c}<br>Total flow: {city_flow_totals[c]}M tons" for c in city_labels],
        showlegend=False,
    )
)

# Update layout
fig.update_layout(
    title={
        "text": "flowmap-origin-destination · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    geo={
        "projection_type": "natural earth",
        "showland": True,
        "landcolor": "rgb(243, 243, 243)",
        "showocean": True,
        "oceancolor": "rgb(230, 240, 250)",
        "showcoastlines": True,
        "coastlinecolor": "rgb(180, 180, 180)",
        "coastlinewidth": 1,
        "showlakes": True,
        "lakecolor": "rgb(230, 240, 250)",
        "showcountries": True,
        "countrycolor": "rgb(200, 200, 200)",
        "countrywidth": 0.5,
        "bgcolor": "rgba(0,0,0,0)",
    },
    paper_bgcolor="white",
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
    annotations=[
        {
            "text": "Line width proportional to trade volume (millions of tons)",
            "x": 0.5,
            "y": -0.02,
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {"size": 16, "color": "#666666"},
        }
    ],
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
