""" pyplots.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 68/100 | Created: 2026-01-20
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColorBar, ColumnDataSource, CustomJSTickFormatter, HoverTool, LinearColorMapper
from bokeh.plotting import figure
from bokeh.transform import transform
from bokeh.util.hex import hexbin


# Data - Simulated GPS coordinates (NYC taxi pickups)
np.random.seed(42)

# Generate clustered point data to simulate urban hotspots
n_points = 5000

# Create multiple cluster centers (simulating different neighborhoods in NYC)
centers = [
    (-73.98, 40.75),  # Midtown Manhattan
    (-73.96, 40.78),  # Upper East Side
    (-74.00, 40.72),  # West Village
    (-73.99, 40.73),  # Greenwich Village
    (-73.97, 40.76),  # Central Park South
]

# Generate points around cluster centers with varying densities
lon_data = []
lat_data = []
for center_lon, center_lat in centers:
    n_cluster = n_points // len(centers) + np.random.randint(-200, 200)
    lon_data.extend(np.random.normal(center_lon, 0.015, n_cluster))
    lat_data.extend(np.random.normal(center_lat, 0.012, n_cluster))

lon = np.array(lon_data)
lat = np.array(lat_data)

# Convert lat/lon to Web Mercator projection
k = 6378137  # Earth radius in meters
merc_lon = lon * (k * np.pi / 180.0)
merc_lat = np.log(np.tan((90 + lat) * np.pi / 360.0)) * k

# Compute hexbin aggregation in Web Mercator coordinates
hex_size = 800  # Size in meters (Web Mercator units)
bins = hexbin(merc_lon, merc_lat, hex_size)

# Extract hexagon coordinates and counts
hex_q = bins.q
hex_r = bins.r
hex_counts = bins.counts

# Create ColumnDataSource for hex tiles
hex_source = ColumnDataSource(data={"q": hex_q, "r": hex_r, "counts": hex_counts})

# Create color mapper with viridis-like colors
colors = ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"]
mapper = LinearColorMapper(palette=colors, low=min(hex_counts), high=max(hex_counts))

# Calculate bounds for the map (with padding)
x_min, x_max = merc_lon.min() - 2000, merc_lon.max() + 2000
y_min, y_max = merc_lat.min() - 2000, merc_lat.max() + 2000

# Simplified Manhattan coastline coordinates (approximate)
manhattan_coast_lon = np.array(
    [-74.047, -74.041, -74.019, -74.009, -73.971, -73.968, -73.943, -73.934, -73.921, -73.911, -73.929, -73.942]
)
manhattan_coast_lat = np.array(
    [40.689, 40.701, 40.705, 40.714, 40.728, 40.751, 40.776, 40.794, 40.806, 40.874, 40.879, 40.873]
)
manhattan_coast_x = manhattan_coast_lon * (k * np.pi / 180.0)
manhattan_coast_y = np.log(np.tan((90 + manhattan_coast_lat) * np.pi / 360.0)) * k

# Hudson River west boundary (approximate)
hudson_lon = np.array([-74.065, -74.055, -74.045, -74.035, -74.025, -74.020, -74.015, -74.010, -74.005])
hudson_lat = np.array([40.68, 40.72, 40.74, 40.76, 40.78, 40.80, 40.82, 40.84, 40.88])
hudson_x = hudson_lon * (k * np.pi / 180.0)
hudson_y = np.log(np.tan((90 + hudson_lat) * np.pi / 360.0)) * k

# East River boundary (approximate)
east_lon = np.array([-73.90, -73.91, -73.92, -73.93, -73.94, -73.95, -73.96, -73.97, -73.98])
east_lat = np.array([40.88, 40.84, 40.80, 40.77, 40.74, 40.72, 40.70, 40.69, 40.68])
east_x = east_lon * (k * np.pi / 180.0)
east_y = np.log(np.tan((90 + east_lat) * np.pi / 360.0)) * k

# Create figure with standard axes (not mercator axis type to avoid tick format issues)
p = figure(
    width=4800,
    height=2700,
    title="hexbin-map-geographic · bokeh · pyplots.ai",
    x_axis_label="Longitude",
    y_axis_label="Latitude",
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
    tools="pan,wheel_zoom,box_zoom,reset",
    background_fill_color="#d4e6f1",  # Light blue for water
)

# Draw land mass background (simplified Manhattan/NYC area)
land_x = [-8250000, -8250000, -8215000, -8215000]
land_y = [4960000, 5010000, 5010000, 4960000]
p.patch(land_x, land_y, fill_color="#e8e4d8", fill_alpha=0.8, line_color=None)

# Draw coastline boundaries for geographic context
p.line(manhattan_coast_x, manhattan_coast_y, line_width=4, line_color="#5d6d7e", alpha=0.7)
p.line(hudson_x, hudson_y, line_width=4, line_color="#5d6d7e", alpha=0.7, line_dash="dashed")
p.line(east_x, east_y, line_width=4, line_color="#5d6d7e", alpha=0.7, line_dash="dashed")

# Plot hex tiles using ColumnDataSource
p.hex_tile(
    q="q",
    r="r",
    size=hex_size,
    fill_color=transform("counts", mapper),
    line_color="#333333",
    line_width=0.5,
    alpha=0.8,
    source=hex_source,
)

# Add hover tool for interactivity
hover = HoverTool(tooltips=[("Pickup Count", "@counts"), ("Cell (q, r)", "(@q, @r)")], mode="mouse")
p.add_tools(hover)

# Add color bar legend with larger text for 4800x2700 canvas
color_bar = ColorBar(
    color_mapper=mapper,
    location=(0, 0),
    title="Pickup Count",
    title_text_font_size="28pt",
    title_text_font_style="bold",
    major_label_text_font_size="22pt",
    width=50,
    padding=20,
    margin=30,
)
p.add_layout(color_bar, "right")

# Style the plot with larger text sizes for 4800x2700 canvas
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling - subtle grid for geographic reference
p.xgrid.grid_line_color = "#999999"
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_color = "#999999"
p.ygrid.grid_line_alpha = 0.3

# Format axis ticks to show degrees instead of Web Mercator meters
lon_formatter = CustomJSTickFormatter(code="return (tick / (6378137 * Math.PI / 180)).toFixed(2) + '°'")
lat_formatter = CustomJSTickFormatter(
    code="return (Math.atan(Math.exp(tick / 6378137)) * 360 / Math.PI - 90).toFixed(2) + '°'"
)
p.xaxis.formatter = lon_formatter
p.yaxis.formatter = lat_formatter

# Save PNG output
export_png(p, filename="plot.png")

# Save interactive HTML (with tile layer for full interactivity)
output_file("plot.html")
p_html = figure(
    width=4800,
    height=2700,
    title="hexbin-map-geographic · bokeh · pyplots.ai",
    x_axis_label="Longitude",
    y_axis_label="Latitude",
    x_axis_type="mercator",
    y_axis_type="mercator",
    x_range=(x_min, x_max),
    y_range=(y_min, y_max),
    tools="pan,wheel_zoom,box_zoom,reset",
)
p_html.add_tile("CartoDB Positron")
p_html.hex_tile(
    q="q",
    r="r",
    size=hex_size,
    fill_color=transform("counts", mapper),
    line_color="#333333",
    line_width=0.5,
    alpha=0.8,
    source=hex_source,
)
p_html.add_tools(hover)
p_html.add_layout(color_bar, "right")
p_html.title.text_font_size = "36pt"
p_html.title.text_font_style = "bold"
p_html.xaxis.axis_label_text_font_size = "28pt"
p_html.yaxis.axis_label_text_font_size = "28pt"
p_html.xaxis.major_label_text_font_size = "22pt"
p_html.yaxis.major_label_text_font_size = "22pt"
save(p_html)
