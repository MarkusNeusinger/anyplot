""" pyplots.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: plotly 6.5.1 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Data: Major world cities with population (in millions)
np.random.seed(42)

cities = [
    {"city": "Tokyo", "lat": 35.6762, "lon": 139.6503, "pop": 37.4, "region": "Asia"},
    {"city": "Delhi", "lat": 28.7041, "lon": 77.1025, "pop": 31.2, "region": "Asia"},
    {"city": "Shanghai", "lat": 31.2304, "lon": 121.4737, "pop": 27.8, "region": "Asia"},
    {"city": "São Paulo", "lat": -23.5505, "lon": -46.6333, "pop": 22.4, "region": "South America"},
    {"city": "Mexico City", "lat": 19.4326, "lon": -99.1332, "pop": 21.9, "region": "North America"},
    {"city": "Cairo", "lat": 30.0444, "lon": 31.2357, "pop": 21.3, "region": "Africa"},
    {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777, "pop": 20.7, "region": "Asia"},
    {"city": "Beijing", "lat": 39.9042, "lon": 116.4074, "pop": 20.5, "region": "Asia"},
    {"city": "Dhaka", "lat": 23.8103, "lon": 90.4125, "pop": 22.5, "region": "Asia"},
    {"city": "Osaka", "lat": 34.6937, "lon": 135.5023, "pop": 19.2, "region": "Asia"},
    {"city": "New York", "lat": 40.7128, "lon": -74.0060, "pop": 18.8, "region": "North America"},
    {"city": "Karachi", "lat": 24.8607, "lon": 67.0011, "pop": 16.5, "region": "Asia"},
    {"city": "Buenos Aires", "lat": -34.6037, "lon": -58.3816, "pop": 15.2, "region": "South America"},
    {"city": "Istanbul", "lat": 41.0082, "lon": 28.9784, "pop": 15.4, "region": "Europe"},
    {"city": "Lagos", "lat": 6.5244, "lon": 3.3792, "pop": 14.9, "region": "Africa"},
    {"city": "Manila", "lat": 14.5995, "lon": 120.9842, "pop": 14.4, "region": "Asia"},
    {"city": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729, "pop": 13.5, "region": "South America"},
    {"city": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "pop": 12.5, "region": "North America"},
    {"city": "Moscow", "lat": 55.7558, "lon": 37.6173, "pop": 12.5, "region": "Europe"},
    {"city": "Paris", "lat": 48.8566, "lon": 2.3522, "pop": 11.1, "region": "Europe"},
    {"city": "London", "lat": 51.5074, "lon": -0.1278, "pop": 9.5, "region": "Europe"},
    {"city": "Lima", "lat": -12.0464, "lon": -77.0428, "pop": 10.9, "region": "South America"},
    {"city": "Bangkok", "lat": 13.7563, "lon": 100.5018, "pop": 10.7, "region": "Asia"},
    {"city": "Jakarta", "lat": -6.2088, "lon": 106.8456, "pop": 10.6, "region": "Asia"},
    {"city": "Seoul", "lat": 37.5665, "lon": 126.9780, "pop": 9.9, "region": "Asia"},
    {"city": "Sydney", "lat": -33.8688, "lon": 151.2093, "pop": 5.4, "region": "Oceania"},
    {"city": "Melbourne", "lat": -37.8136, "lon": 144.9631, "pop": 5.0, "region": "Oceania"},
    {"city": "Toronto", "lat": 43.6532, "lon": -79.3832, "pop": 6.3, "region": "North America"},
    {"city": "Chicago", "lat": 41.8781, "lon": -87.6298, "pop": 8.9, "region": "North America"},
    {"city": "Singapore", "lat": 1.3521, "lon": 103.8198, "pop": 5.9, "region": "Asia"},
]

df = pd.DataFrame(cities)

# Scale bubble sizes: area proportional to population
# Using sqrt to make area proportional (since marker size is diameter)
min_size = 15
max_size = 70
df["marker_size"] = min_size + (max_size - min_size) * np.sqrt(
    (df["pop"] - df["pop"].min()) / (df["pop"].max() - df["pop"].min())
)

# Color palette for regions (colorblind-safe)
region_colors = {
    "Asia": "#306998",  # Python Blue
    "Europe": "#FFD43B",  # Python Yellow
    "North America": "#2ca02c",  # Green
    "South America": "#ff7f0e",  # Orange
    "Africa": "#9467bd",  # Purple
    "Oceania": "#17becf",  # Cyan
}

# Create figure with geo map
fig = go.Figure()

# Add traces for each region to create proper legend
for region in df["region"].unique():
    region_df = df[df["region"] == region]
    fig.add_trace(
        go.Scattergeo(
            lon=region_df["lon"],
            lat=region_df["lat"],
            text=region_df.apply(lambda x: f"{x['city']}<br>Population: {x['pop']:.1f}M", axis=1),
            marker={
                "size": region_df["marker_size"],
                "color": region_colors[region],
                "opacity": 0.65,
                "line": {"width": 1.5, "color": "white"},
                "sizemode": "diameter",
            },
            name=region,
            hovertemplate="%{text}<extra></extra>",
        )
    )

# Update layout for 4800x2700
fig.update_layout(
    title={
        "text": "World City Populations · bubble-map-geographic · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#333333"},
        "x": 0.5,
        "xanchor": "center",
    },
    geo={
        "showland": True,
        "landcolor": "rgb(243, 243, 243)",
        "showocean": True,
        "oceancolor": "rgb(230, 240, 250)",
        "showcoastlines": True,
        "coastlinecolor": "rgb(150, 150, 150)",
        "coastlinewidth": 1,
        "showframe": True,
        "framecolor": "rgb(100, 100, 100)",
        "framewidth": 1,
        "showcountries": True,
        "countrycolor": "rgb(200, 200, 200)",
        "countrywidth": 0.5,
        "projection_type": "natural earth",
        "lataxis": {"range": [-60, 75]},
        "lonaxis": {"range": [-140, 180]},
    },
    legend={
        "title": {"text": "Region", "font": {"size": 20}},
        "font": {"size": 18},
        "itemsizing": "constant",
        "x": 0.02,
        "y": 0.35,
        "bgcolor": "rgba(255,255,255,0.85)",
        "bordercolor": "rgba(0,0,0,0.2)",
        "borderwidth": 1,
    },
    margin={"l": 20, "r": 20, "t": 80, "b": 20},
    template="plotly_white",
)

# Add size legend annotation
fig.add_annotation(
    text="Bubble size = Population (millions)",
    xref="paper",
    yref="paper",
    x=0.02,
    y=0.15,
    showarrow=False,
    font={"size": 16, "color": "#555555"},
    align="left",
)

# Example size indicators
size_examples = [5, 20, 35]
for i, pop_val in enumerate(size_examples):
    size = min_size + (max_size - min_size) * np.sqrt((pop_val - df["pop"].min()) / (df["pop"].max() - df["pop"].min()))
    fig.add_annotation(
        text=f"  {pop_val}M",
        xref="paper",
        yref="paper",
        x=0.065,
        y=0.09 - i * 0.028,
        showarrow=False,
        font={"size": 14, "color": "#666666"},
        align="left",
    )

# Save as PNG (4800x2700)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
