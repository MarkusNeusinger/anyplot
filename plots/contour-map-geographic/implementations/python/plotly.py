""" pyplots.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-17
"""

import numpy as np
import plotly.graph_objects as go


# Data - Simulated surface temperature over North Atlantic region
np.random.seed(42)

# Define grid over North Atlantic (30N to 60N, -60W to 0E)
lat_range = np.linspace(30, 60, 50)
lon_range = np.linspace(-60, 0, 50)
lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)

# Create realistic temperature pattern:
# - Cooler in the north, warmer in the south
# - Gulf Stream effect (warmer on eastern side)
# - Some natural variation
base_temp = 20 - 0.5 * (lat_grid - 30)  # Latitude gradient
gulf_stream = 3 * np.exp(-((lon_grid + 30) ** 2) / 400)  # Gulf Stream warming
variation = 2 * np.sin(lat_grid / 5) * np.cos(lon_grid / 8)  # Natural variation
temperature = base_temp + gulf_stream + variation

# Create figure with geographic projection
fig = go.Figure()

# Add filled contours on geographic map
fig.add_trace(
    go.Contour(
        x=lon_range,
        y=lat_range,
        z=temperature,
        contours={"start": 0, "end": 22, "size": 2, "showlabels": True, "labelfont": {"size": 14, "color": "white"}},
        colorscale="RdYlBu_r",  # Red (warm) to Blue (cold), reversed
        colorbar={
            "title": {"text": "Temperature (°C)", "font": {"size": 18}},
            "tickfont": {"size": 14},
            "len": 0.75,
            "thickness": 20,
        },
        line={"width": 2, "color": "rgba(50,50,50,0.5)"},
        hovertemplate="Lat: %{y:.1f}°N<br>Lon: %{x:.1f}°W<br>Temp: %{z:.1f}°C<extra></extra>",
    )
)

# Update layout with geographic styling
fig.update_layout(
    title={
        "text": "North Atlantic Sea Surface Temperature · contour-map-geographic · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Longitude", "font": {"size": 22}},
        "tickfont": {"size": 16},
        "ticksuffix": "°",
        "dtick": 10,
        "showgrid": True,
        "gridcolor": "rgba(128,128,128,0.3)",
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Latitude", "font": {"size": 22}},
        "tickfont": {"size": 16},
        "ticksuffix": "°N",
        "dtick": 5,
        "showgrid": True,
        "gridcolor": "rgba(128,128,128,0.3)",
        "zeroline": False,
        "scaleanchor": "x",
        "scaleratio": 1,
    },
    template="plotly_white",
    margin={"l": 80, "r": 120, "t": 100, "b": 80},
)

# Add geographic reference annotations for key locations
annotations = [
    {"x": -50, "y": 47, "text": "Newfoundland", "showarrow": False, "font": {"size": 14, "color": "gray"}},
    {"x": -10, "y": 50, "text": "Ireland", "showarrow": False, "font": {"size": 14, "color": "gray"}},
    {"x": -20, "y": 37, "text": "Azores", "showarrow": False, "font": {"size": 14, "color": "gray"}},
]
fig.update_layout(annotations=annotations)

# Save as PNG (4800x2700 via scale)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
