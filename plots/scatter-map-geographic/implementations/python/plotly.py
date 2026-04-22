""" pyplots.ai
scatter-map-geographic: Scatter Map with Geographic Points
Library: plotly 6.5.1 | Python 3.13.11
Quality: 92/100 | Created: 2026-01-10
"""

import numpy as np
import plotly.graph_objects as go


# Data: Global earthquake locations with magnitude
np.random.seed(42)

# Earthquake epicenters distributed across tectonic zones
n_points = 80

# Pacific Ring of Fire
n_pacific = 30
pacific_lat = np.concatenate(
    [
        np.random.uniform(35, 45, 10),  # Japan
        np.random.uniform(-5, 5, 10),  # Indonesia
        np.random.uniform(-40, -20, 10),  # Chile
    ]
)
pacific_lon = np.concatenate(
    [
        np.random.uniform(135, 145, 10),  # Japan
        np.random.uniform(100, 130, 10),  # Indonesia
        np.random.uniform(-75, -70, 10),  # Chile
    ]
)

# Mediterranean-Himalayan belt
n_med = 20
med_lat = np.concatenate(
    [
        np.random.uniform(35, 42, 10),  # Mediterranean
        np.random.uniform(25, 35, 10),  # Himalayas
    ]
)
med_lon = np.concatenate(
    [
        np.random.uniform(15, 35, 10),  # Mediterranean
        np.random.uniform(75, 95, 10),  # Himalayas
    ]
)

# Mid-Atlantic Ridge
n_atlantic = 15
atlantic_lat = np.random.uniform(-30, 60, n_atlantic)
atlantic_lon = np.random.uniform(-35, -25, n_atlantic)

# Scattered other locations
n_other = n_points - n_pacific - n_med - n_atlantic
other_lat = np.random.uniform(-50, 60, n_other)
other_lon = np.random.uniform(-120, 150, n_other)

# Combine all data
latitudes = np.concatenate([pacific_lat, med_lat, atlantic_lat, other_lat])
longitudes = np.concatenate([pacific_lon, med_lon, atlantic_lon, other_lon])

# Earthquake magnitudes (Richter scale) - higher in active zones
magnitudes = np.concatenate(
    [
        np.random.uniform(4.5, 7.5, n_pacific),  # Pacific - stronger
        np.random.uniform(4.0, 6.5, n_med),  # Mediterranean-Himalayan
        np.random.uniform(3.5, 5.5, n_atlantic),  # Mid-Atlantic - moderate
        np.random.uniform(3.0, 5.0, n_other),  # Other areas - weaker
    ]
)

# Depth in km
depths = np.random.uniform(5, 300, n_points)

# Size scaling based on magnitude (larger = stronger earthquake)
sizes = (magnitudes - magnitudes.min()) / (magnitudes.max() - magnitudes.min())
sizes = sizes * 25 + 8  # Scale to 8-33 range for visibility

# Create hover text
hover_texts = [f"Mag: {m:.1f}, Depth: {d:.0f}km" for m, d in zip(magnitudes, depths, strict=True)]

# Create figure with geographic scatter
fig = go.Figure()

fig.add_trace(
    go.Scattergeo(
        lat=latitudes,
        lon=longitudes,
        mode="markers",
        marker={
            "size": sizes,
            "color": depths,
            "colorscale": "Viridis",
            "colorbar": {
                "title": {"text": "Depth (km)", "font": {"size": 20}},
                "tickfont": {"size": 16},
                "len": 0.6,
                "thickness": 25,
                "x": 1.02,
            },
            "line": {"width": 1, "color": "white"},
            "opacity": 0.8,
        },
        text=hover_texts,
        hovertemplate="<b>Lat:</b> %{lat:.2f}°<br><b>Lon:</b> %{lon:.2f}°<br>%{text}<extra></extra>",
    )
)

# Layout with geographic projection
fig.update_layout(
    title={"text": "scatter-map-geographic · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    geo={
        "projection_type": "natural earth",
        "showland": True,
        "landcolor": "#E5E5E5",
        "showocean": True,
        "oceancolor": "#D4E8F2",
        "showcoastlines": True,
        "coastlinecolor": "#666666",
        "coastlinewidth": 1,
        "showcountries": True,
        "countrycolor": "#999999",
        "countrywidth": 0.5,
        "showlakes": True,
        "lakecolor": "#D4E8F2",
        "bgcolor": "white",
    },
    template="plotly_white",
    margin={"l": 20, "r": 100, "t": 80, "b": 20},
)

# Add size legend annotation
fig.add_annotation(
    x=1.02,
    y=0.15,
    xref="paper",
    yref="paper",
    text="<b>Point Size</b><br>= Magnitude",
    showarrow=False,
    font={"size": 16},
    align="left",
)

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
