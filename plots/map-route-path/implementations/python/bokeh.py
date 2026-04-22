""" pyplots.ai
map-route-path: Route Path Map
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-19
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Title
from bokeh.plotting import figure


# Data - Simulated hiking trail GPS track (approximately 200 waypoints)
np.random.seed(42)

# Base coordinates (Central Park, New York area)
center_lon = -73.968
center_lat = 40.785

# Generate a realistic hiking trail path with sequential waypoints
n_points = 200
t = np.linspace(0, 4 * np.pi, n_points)

# Create a winding path with some randomness (simulating trail GPS data)
lat_offset = 0.015 * np.sin(t) + 0.008 * np.sin(2.5 * t) + 0.002 * np.cumsum(np.random.randn(n_points)) / n_points
lon_offset = 0.012 * np.cos(t) + 0.006 * np.cos(3 * t) + 0.002 * np.cumsum(np.random.randn(n_points)) / n_points

lats = center_lat + lat_offset
lons = center_lon + lon_offset

# Convert lat/lon to Web Mercator coordinates (required for tile providers)
k = 20037508.34 / 180
x_coords = lons * k
y_coords = np.log(np.tan((90 + lats) * np.pi / 360)) / (np.pi / 180) * k

# Sequence and color gradient for time progression
sequence = np.arange(n_points)
colors = [
    f"#{int(50 + 150 * i / n_points):02x}{int(105 - 80 * i / n_points):02x}{int(152 - 100 * i / n_points):02x}"
    for i in range(n_points)
]

# Create ColumnDataSource for the path
source = ColumnDataSource(data={"x": x_coords, "y": y_coords, "sequence": sequence, "color": colors})

# Create figure with tile background
p = figure(
    width=4800,
    height=2700,
    x_axis_type="mercator",
    y_axis_type="mercator",
    x_axis_label="Longitude",
    y_axis_label="Latitude",
    tools="pan,wheel_zoom,box_zoom,reset",
)

# Add title separately for better control
p.add_layout(Title(text="map-route-path · bokeh · pyplots.ai", text_font_size="28pt"), "above")

# Add basemap tiles (Bokeh 3.x uses add_tile with string provider name)
p.add_tile("CartoDB Positron")

# Draw the route path as connected line
p.line(x="x", y="y", source=source, line_width=4, line_color="#306998", line_alpha=0.8)

# Add points along the path with color gradient showing progression
p.scatter(x="x", y="y", source=source, size=8, fill_color="color", line_color="#306998", line_width=1, alpha=0.7)

# Mark start point (green circle)
start_source = ColumnDataSource(data={"x": [x_coords[0]], "y": [y_coords[0]]})
p.scatter(
    x="x",
    y="y",
    source=start_source,
    size=25,
    fill_color="#2ecc71",
    line_color="white",
    line_width=3,
    legend_label="Start",
)

# Mark end point (red square)
end_source = ColumnDataSource(data={"x": [x_coords[-1]], "y": [y_coords[-1]]})
p.scatter(
    x="x",
    y="y",
    source=end_source,
    size=25,
    fill_color="#e74c3c",
    line_color="white",
    line_width=3,
    marker="square",
    legend_label="End",
)

# Styling
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Legend styling
p.legend.location = "top_right"
p.legend.label_text_font_size = "18pt"
p.legend.background_fill_alpha = 0.8

# Grid styling
p.grid.grid_line_alpha = 0.3

# Save outputs
export_png(p, filename="plot.png")

# Save interactive HTML for bokeh
output_file("plot.html")
save(p)
