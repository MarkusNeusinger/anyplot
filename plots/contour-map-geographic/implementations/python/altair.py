""" pyplots.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: altair 6.0.0 | Python 3.13.11
Quality: 82/100 | Created: 2026-01-17
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Generate temperature-like data for Europe region
np.random.seed(42)

# Create dense grid covering wider Europe region to fill map canvas
lon_range = np.linspace(-25, 55, 140)
lat_range = np.linspace(30, 72, 90)
lon_grid, lat_grid = np.meshgrid(lon_range, lat_range)

# Generate temperature pattern (decreases with latitude, varies with longitude)
temperature = (
    30
    - 0.6 * (lat_grid - 30)  # Cooler as you go north
    + 3 * np.sin((lon_grid + 10) / 15)  # East-west variation (Gulf Stream effect)
    + 2 * np.cos(lat_grid / 10)  # Additional pattern
    - 5 * np.exp(-((lat_grid - 47) ** 2 + (lon_grid - 10) ** 2) / 100)  # Alps cold spot
    - 3 * np.exp(-((lat_grid - 65) ** 2 + (lon_grid - 25) ** 2) / 150)  # Scandinavian cold
    + np.random.normal(0, 0.3, lon_grid.shape)  # Minimal noise for smoother contours
)

# Clip to realistic range
temperature = np.clip(temperature, -15, 35)

# Create DataFrame
df = pd.DataFrame(
    {"longitude": lon_grid.flatten(), "latitude": lat_grid.flatten(), "temperature": temperature.flatten()}
)

# Define contour levels for labeling
contour_levels = [-10, -5, 0, 5, 10, 15, 20, 25, 30]

# Load world countries for geographic context
countries = alt.topo_feature("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json", "countries")

# Map projection settings - centered on Europe with better coverage
projection_params = {"type": "mercator", "scale": 550, "center": [15, 52]}

# Base map - world countries with subtle styling
base = (
    alt.Chart(countries)
    .mark_geoshape(fill="#E8E8E8", stroke="#AAAAAA", strokeWidth=0.5)
    .project(**projection_params)
    .properties(width=1600, height=900)
)

# Create smooth filled contour visualization using mark_square for cleaner coverage
filled_contours = (
    alt.Chart(df)
    .mark_square(size=200, opacity=0.92)
    .encode(
        longitude="longitude:Q",
        latitude="latitude:Q",
        color=alt.Color(
            "temperature:Q",
            scale=alt.Scale(scheme="redyellowblue", reverse=True, domain=[-10, 30]),
            legend=alt.Legend(
                title="Temperature (°C)",
                titleFontSize=20,
                labelFontSize=16,
                gradientLength=450,
                gradientThickness=30,
                orient="right",
                offset=20,
            ),
        ),
        tooltip=[
            alt.Tooltip("longitude:Q", format=".1f", title="Longitude"),
            alt.Tooltip("latitude:Q", format=".1f", title="Latitude"),
            alt.Tooltip("temperature:Q", format=".1f", title="Temperature (°C)"),
        ],
    )
    .project(**projection_params)
    .properties(width=1600, height=900)
)

# Create contour line data by identifying boundary points between temperature bins
# Use tighter threshold for cleaner isolines
contour_data = []
for level in contour_levels[1:-1]:  # Skip extreme ends
    mask = np.abs(df["temperature"] - level) < 0.5
    level_points = df[mask].copy()
    level_points["contour_value"] = level
    level_points["contour_label"] = f"{level}°C"
    contour_data.append(level_points)

contour_df = pd.concat(contour_data, ignore_index=True)

# Contour lines layer - more prominent strokes forming isolines
contour_lines = (
    alt.Chart(contour_df)
    .mark_circle(size=25, opacity=0.85)
    .encode(longitude="longitude:Q", latitude="latitude:Q", color=alt.value("#1a1a1a"))
    .project(**projection_params)
    .properties(width=1600, height=900)
)

# Create contour labels at strategic positions
# Sample representative points along each contour level for labeling
label_data = []
for level in [0, 10, 20]:
    level_points = contour_df[contour_df["contour_value"] == level]
    if len(level_points) > 0:
        # Select points at different longitudes for label placement
        for target_lon in [-10, 10, 30]:
            closest_idx = (level_points["longitude"] - target_lon).abs().idxmin()
            point = level_points.loc[closest_idx].copy()
            label_data.append({"longitude": point["longitude"], "latitude": point["latitude"], "label": f"{level}°C"})

label_df = pd.DataFrame(label_data)

# Contour value labels with higher contrast
contour_labels = (
    alt.Chart(label_df)
    .mark_text(fontSize=18, fontWeight="bold", fill="#000000", stroke="#FFFFFF", strokeWidth=3)
    .encode(longitude="longitude:Q", latitude="latitude:Q", text="label:N")
    .project(**projection_params)
    .properties(width=1600, height=900)
)

# Create latitude/longitude axis labels for map edges
# Longitude labels along bottom
lon_labels_data = pd.DataFrame({"longitude": [-20, -10, 0, 10, 20, 30, 40, 50], "latitude": [31] * 8})
lon_labels_data["label"] = lon_labels_data["longitude"].apply(
    lambda x: f"{abs(x)}°{'W' if x < 0 else 'E'}" if x != 0 else "0°"
)

lon_axis_labels = (
    alt.Chart(lon_labels_data)
    .mark_text(fontSize=14, fontWeight="normal", fill="#333333", dy=12)
    .encode(longitude="longitude:Q", latitude="latitude:Q", text="label:N")
    .project(**projection_params)
    .properties(width=1600, height=900)
)

# Latitude labels along left edge
lat_labels_data = pd.DataFrame({"longitude": [-24] * 5, "latitude": [35, 45, 55, 65, 70]})
lat_labels_data["label"] = lat_labels_data["latitude"].apply(lambda x: f"{x}°N")

lat_axis_labels = (
    alt.Chart(lat_labels_data)
    .mark_text(fontSize=14, fontWeight="normal", fill="#333333", dx=-12, align="right")
    .encode(longitude="longitude:Q", latitude="latitude:Q", text="label:N")
    .project(**projection_params)
    .properties(width=1600, height=900)
)

# Layer all components: base map, filled contours, contour lines, labels, axis labels
chart = (
    alt.layer(base, filled_contours, contour_lines, contour_labels, lon_axis_labels, lat_axis_labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title("contour-map-geographic · altair · pyplots.ai", fontSize=28, anchor="middle", color="#333333"),
    )
    .configure_view(strokeWidth=0)
)

# Save outputs
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")
