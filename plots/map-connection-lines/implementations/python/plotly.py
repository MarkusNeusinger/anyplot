""" pyplots.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import numpy as np
import plotly.graph_objects as go


# Data: Major global flight routes between airports
np.random.seed(42)

# Define major airports with coordinates (lat, lon)
airports = {
    "JFK": (40.6413, -73.7781, "New York"),
    "LAX": (33.9416, -118.4085, "Los Angeles"),
    "LHR": (51.4700, -0.4543, "London"),
    "CDG": (49.0097, 2.5479, "Paris"),
    "NRT": (35.7720, 140.3929, "Tokyo"),
    "SYD": (-33.9399, 151.1753, "Sydney"),
    "DXB": (25.2532, 55.3657, "Dubai"),
    "SIN": (1.3644, 103.9915, "Singapore"),
    "HKG": (22.3080, 113.9185, "Hong Kong"),
    "FRA": (50.0379, 8.5622, "Frankfurt"),
}

# Define flight routes with passenger volume (thousands per year)
routes = [
    ("JFK", "LHR", 4200),
    ("JFK", "CDG", 2800),
    ("LAX", "NRT", 3100),
    ("LAX", "SYD", 1900),
    ("LHR", "DXB", 3500),
    ("LHR", "SIN", 2200),
    ("LHR", "HKG", 2900),
    ("CDG", "NRT", 1800),
    ("DXB", "SIN", 2600),
    ("DXB", "HKG", 2100),
    ("SIN", "SYD", 2400),
    ("HKG", "NRT", 2700),
    ("FRA", "JFK", 3000),
    ("FRA", "DXB", 2300),
    ("SIN", "NRT", 1600),
]

# Create figure with geographic projection
fig = go.Figure()

# Add flight routes as lines
for origin, dest, passengers in routes:
    origin_lat, origin_lon, origin_city = airports[origin]
    dest_lat, dest_lon, dest_city = airports[dest]

    # Line width scaled by passenger volume (range 2-8)
    width = 2 + (passengers - 1600) / (4200 - 1600) * 6

    # Opacity based on volume
    opacity = 0.4 + (passengers - 1600) / (4200 - 1600) * 0.4

    fig.add_trace(
        go.Scattergeo(
            lon=[origin_lon, dest_lon],
            lat=[origin_lat, dest_lat],
            mode="lines",
            line=dict(width=width, color="#306998"),
            opacity=opacity,
            name=f"{origin_city} → {dest_city}",
            hoverinfo="text",
            text=f"{origin_city} → {dest_city}<br>{passengers}K passengers/year",
            showlegend=False,
        )
    )

# Add airport markers
airport_lons = [airports[code][1] for code in airports]
airport_lats = [airports[code][0] for code in airports]
airport_names = [f"{airports[code][2]} ({code})" for code in airports]

fig.add_trace(
    go.Scattergeo(
        lon=airport_lons,
        lat=airport_lats,
        mode="markers+text",
        marker=dict(size=14, color="#FFD43B", line=dict(width=2, color="#306998")),
        text=[code for code in airports],
        textposition="top center",
        textfont=dict(size=14, color="#306998", family="Arial Black"),
        hoverinfo="text",
        hovertext=airport_names,
        name="Airports",
        showlegend=False,
    )
)

# Update layout with geographic projection
fig.update_layout(
    title=dict(
        text="Global Flight Routes · map-connection-lines · plotly · pyplots.ai",
        font=dict(size=28, color="#306998"),
        x=0.5,
        xanchor="center",
    ),
    geo=dict(
        projection_type="natural earth",
        showland=True,
        landcolor="#f0f0f0",
        showocean=True,
        oceancolor="#e6f2ff",
        showcoastlines=True,
        coastlinecolor="#999999",
        coastlinewidth=1,
        showlakes=True,
        lakecolor="#e6f2ff",
        showcountries=True,
        countrycolor="#cccccc",
        countrywidth=0.5,
        showframe=False,
        bgcolor="white",
    ),
    template="plotly_white",
    margin=dict(l=20, r=20, t=80, b=20),
    annotations=[
        dict(
            text="Line thickness indicates passenger volume (1.6M - 4.2M passengers/year)",
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.02,
            showarrow=False,
            font=dict(size=16, color="#666666"),
        )
    ],
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
