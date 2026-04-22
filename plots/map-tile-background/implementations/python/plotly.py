""" pyplots.ai
map-tile-background: Map with Tile Background
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import plotly.graph_objects as go


# Data - European City Landmarks
np.random.seed(42)

# Major European city landmarks with simulated visitor counts
landmarks = {
    "name": [
        "Eiffel Tower",
        "Colosseum",
        "Sagrada Familia",
        "Big Ben",
        "Brandenburg Gate",
        "Anne Frank House",
        "Acropolis",
        "Charles Bridge",
        "St. Stephen's Basilica",
        "Royal Palace",
        "Manneken Pis",
        "Tivoli Gardens",
        "Schonbrunn Palace",
        "Old Town Square",
        "Rialto Bridge",
    ],
    "lat": [
        48.8584,
        41.8902,
        41.4036,
        51.5007,
        52.5163,
        52.3752,
        37.9715,
        50.0865,
        47.5008,
        59.3268,
        50.8450,
        55.6736,
        48.1845,
        50.0870,
        45.4380,
    ],
    "lon": [
        2.2945,
        12.4922,
        2.1744,
        -0.1246,
        13.3777,
        4.8840,
        23.7267,
        14.4114,
        19.0538,
        18.0717,
        4.3499,
        12.5681,
        16.3119,
        14.4208,
        12.3358,
    ],
    "visitors": [
        7000000,
        7400000,
        4500000,
        2000000,
        3000000,
        1300000,
        3000000,
        5000000,
        1000000,
        1500000,
        500000,
        4000000,
        4000000,
        6000000,
        5000000,
    ],
}

# Convert visitors to marker sizes (scaled for visibility)
visitors = np.array(landmarks["visitors"])
sizes = 15 + (visitors - visitors.min()) / (visitors.max() - visitors.min()) * 35

# Create the map figure with tile background
fig = go.Figure()

# Add scattermap trace for data points on tile background (new API replacing scattermapbox)
fig.add_trace(
    go.Scattermap(
        lat=landmarks["lat"],
        lon=landmarks["lon"],
        mode="markers+text",
        marker=dict(
            size=sizes,
            color=visitors,
            colorscale=[[0, "#306998"], [0.5, "#4a8bc2"], [1, "#FFD43B"]],
            colorbar=dict(
                title=dict(text="Annual Visitors", font=dict(size=18)), tickfont=dict(size=14), thickness=20, len=0.7
            ),
            opacity=0.85,
        ),
        text=landmarks["name"],
        textposition="top center",
        textfont=dict(size=12, color="black"),
        hovertemplate="<b>%{text}</b><br>"
        + "Lat: %{lat:.4f}<br>"
        + "Lon: %{lon:.4f}<br>"
        + "Visitors: %{marker.color:,.0f}<extra></extra>",
    )
)

# Update layout with OpenStreetMap tile background (new 'map' API replacing 'mapbox')
fig.update_layout(
    title=dict(
        text="European Landmarks Visitor Data<br>"
        "<span style='font-size:20px'>map-tile-background \u00b7 plotly \u00b7 pyplots.ai</span>",
        font=dict(size=28),
        x=0.5,
        xanchor="center",
    ),
    map=dict(style="open-street-map", center=dict(lat=48.5, lon=10.0), zoom=3.5),
    margin=dict(l=20, r=20, t=100, b=20),
    showlegend=False,
)

# Save as PNG (4800x2700 at scale 3)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs="cdn")
