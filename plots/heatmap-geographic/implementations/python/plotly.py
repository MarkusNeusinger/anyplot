""" pyplots.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: plotly 6.5.1 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-10
"""

import numpy as np
import plotly.graph_objects as go


# Data - Simulating activity density around San Francisco Bay Area
np.random.seed(42)

# Hotspot 1: Downtown SF
lat1 = np.random.normal(37.79, 0.02, 400)
lon1 = np.random.normal(-122.40, 0.02, 400)
val1 = np.random.uniform(0.6, 1.0, 400)

# Hotspot 2: Oakland
lat2 = np.random.normal(37.80, 0.025, 350)
lon2 = np.random.normal(-122.27, 0.025, 350)
val2 = np.random.uniform(0.5, 0.9, 350)

# Hotspot 3: Berkeley
lat3 = np.random.normal(37.87, 0.015, 250)
lon3 = np.random.normal(-122.26, 0.015, 250)
val3 = np.random.uniform(0.4, 0.8, 250)

# Hotspot 4: South SF
lat4 = np.random.normal(37.65, 0.03, 300)
lon4 = np.random.normal(-122.40, 0.03, 300)
val4 = np.random.uniform(0.3, 0.7, 300)

# Scattered background points
lat_bg = np.random.uniform(37.5, 38.0, 200)
lon_bg = np.random.uniform(-122.6, -122.1, 200)
val_bg = np.random.uniform(0.1, 0.4, 200)

# Combine all data
latitudes = np.concatenate([lat1, lat2, lat3, lat4, lat_bg])
longitudes = np.concatenate([lon1, lon2, lon3, lon4, lon_bg])
values = np.concatenate([val1, val2, val3, val4, val_bg])

# Create the geographic heatmap using Densitymap (new API)
fig = go.Figure()

# Add density heatmap layer
fig.add_trace(
    go.Densitymap(
        lat=latitudes,
        lon=longitudes,
        z=values,
        radius=15,
        colorscale="YlOrRd",
        opacity=0.7,
        showscale=True,
        colorbar={
            "title": {"text": "Intensity", "font": {"size": 20}},
            "tickfont": {"size": 16},
            "len": 0.6,
            "thickness": 25,
            "x": 1.02,
        },
        hovertemplate="Lat: %{lat:.4f}<br>Lon: %{lon:.4f}<br>Value: %{z:.2f}<extra></extra>",
    )
)

# Update layout for geographic display
fig.update_layout(
    title={
        "text": "Activity Density in SF Bay Area · heatmap-geographic · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    map={"style": "carto-positron", "center": {"lat": 37.75, "lon": -122.35}, "zoom": 9.5},
    margin={"l": 20, "r": 100, "t": 80, "b": 20},
    template="plotly_white",
)

# Save as PNG
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML version
fig.write_html("plot.html", include_plotlyjs="cdn")
