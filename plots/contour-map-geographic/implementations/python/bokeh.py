""" pyplots.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-17
"""

import matplotlib.pyplot as plt
import numpy as np
from bokeh.io import export_png
from bokeh.models import ColorBar, ColumnDataSource, LabelSet, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure


# Data - Simulated elevation data for Pacific Northwest region
np.random.seed(42)

# Geographic region: Pacific Northwest coast (simplified)
lat_min, lat_max = 42.0, 49.0  # Oregon to Washington
lon_min, lon_max = -125.0, -117.0  # Pacific coast inland

# Create grid
n_points = 50
lons = np.linspace(lon_min, lon_max, n_points)
lats = np.linspace(lat_min, lat_max, n_points)
lon_grid, lat_grid = np.meshgrid(lons, lats)

# Generate realistic elevation data with mountain ranges
# Base elevation increases from coast (west) to inland (east)
base_elevation = (lon_grid - lon_min) / (lon_max - lon_min) * 1000

# Add Cascade Range (north-south mountain range)
cascade_center_lon = -121.5
cascade_width = 1.0
cascade_height = np.exp(-((lon_grid - cascade_center_lon) ** 2) / (2 * cascade_width**2))
cascade_elevation = cascade_height * 3000 * (1 + 0.3 * np.sin(lat_grid * 2))

# Add some random terrain variation
terrain_noise = np.random.randn(n_points, n_points) * 100
for _ in range(3):
    terrain_noise = (
        np.roll(terrain_noise, 1, axis=0)
        + np.roll(terrain_noise, -1, axis=0)
        + np.roll(terrain_noise, 1, axis=1)
        + np.roll(terrain_noise, -1, axis=1)
    ) / 4

elevation = base_elevation + cascade_elevation + terrain_noise
elevation = np.clip(elevation, 0, None)  # No negative elevation

# Contour levels (every 250 meters)
levels = np.arange(0, 3500, 250)

# Use matplotlib to extract contour paths (we only use it for contour extraction, not plotting)
fig_temp, ax_temp = plt.subplots()
contour_set = ax_temp.contour(lon_grid, lat_grid, elevation, levels=levels)
plt.close(fig_temp)

# Create Bokeh figure
p = figure(
    width=4800,
    height=2700,
    title="contour-map-geographic · bokeh · pyplots.ai",
    x_axis_label="Longitude (°W)",
    y_axis_label="Latitude (°N)",
    x_range=(lon_min, lon_max),
    y_range=(lat_min, lat_max),
    tools="pan,wheel_zoom,box_zoom,reset",
)

# Style the figure
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Add filled contours using image
color_mapper = LinearColorMapper(palette=Viridis256, low=0, high=3000)

# Display the elevation as a background image
p.image(
    image=[elevation],
    x=lon_min,
    y=lat_min,
    dw=lon_max - lon_min,
    dh=lat_max - lat_min,
    color_mapper=color_mapper,
    alpha=0.7,
)

# Draw contour lines extracted from matplotlib
contour_colors = ["#000000", "#333333", "#555555", "#777777"]
label_data = {"x": [], "y": [], "text": []}

for i, (level, paths) in enumerate(zip(contour_set.levels, contour_set.allsegs, strict=True)):
    if level == 0:
        continue  # Skip zero level

    for path in paths:
        if len(path) < 5:
            continue

        contour_lons = path[:, 0]
        contour_lats = path[:, 1]

        # Draw contour line - thicker lines for better visibility
        line_color = contour_colors[i % len(contour_colors)]
        line_width = 4 if level % 1000 == 0 else 2.5

        p.line(x=contour_lons, y=contour_lats, line_color=line_color, line_width=line_width, line_alpha=0.9)

        # Add label at midpoint for major contours (every 500m)
        if level % 500 == 0 and len(path) > 20:
            mid_idx = len(path) // 2
            label_data["x"].append(contour_lons[mid_idx])
            label_data["y"].append(contour_lats[mid_idx])
            label_data["text"].append(f"{int(level)}m")

# Add contour labels - larger font for 4800x2700 canvas
label_source = ColumnDataSource(data=label_data)
labels = LabelSet(
    x="x",
    y="y",
    text="text",
    source=label_source,
    text_font_size="20pt",
    text_color="black",
    text_font_style="bold",
    background_fill_color="white",
    background_fill_alpha=0.85,
)
p.add_layout(labels)

# Add simplified coastline representation (approximate Pacific coast)
coast_lons = [-125.0, -124.8, -124.5, -124.2, -124.0, -123.8, -124.0, -124.3, -124.5]
coast_lats = [42.0, 43.5, 45.0, 46.0, 46.5, 47.5, 48.0, 48.5, 49.0]
p.line(x=coast_lons, y=coast_lats, line_color="#306998", line_width=4, legend_label="Coastline (approx.)")

# Add colorbar
color_bar = ColorBar(
    color_mapper=color_mapper,
    label_standoff=12,
    width=40,
    location=(0, 0),
    title="Elevation (m)",
    title_text_font_size="18pt",
    major_label_text_font_size="14pt",
)
p.add_layout(color_bar, "right")

# Configure legend - position outside plot area to avoid overlap
p.legend.location = "bottom_right"
p.legend.label_text_font_size = "16pt"
p.legend.background_fill_alpha = 0.9
p.legend.border_line_alpha = 0.5

# Grid styling - subtle solid lines
p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2
p.xgrid.grid_line_color = "#666666"
p.ygrid.grid_line_color = "#666666"

# Save
export_png(p, filename="plot.png")
