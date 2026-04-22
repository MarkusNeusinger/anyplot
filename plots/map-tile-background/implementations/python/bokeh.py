""" pyplots.ai
map-tile-background: Map with Tile Background
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import xyzservices.providers as xyz
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure


# Data: European capital cities with visitor counts (millions per year)
np.random.seed(42)

# City coordinates (lon, lat)
cities = {
    "Paris": (2.3522, 48.8566),
    "London": (-0.1276, 51.5074),
    "Rome": (12.4964, 41.9028),
    "Barcelona": (2.1734, 41.3851),
    "Amsterdam": (4.9041, 52.3676),
    "Berlin": (13.4050, 52.5200),
    "Prague": (14.4378, 50.0755),
    "Vienna": (16.3738, 48.2082),
    "Madrid": (-3.7038, 40.4168),
    "Lisbon": (-9.1393, 38.7223),
    "Brussels": (4.3517, 50.8503),
    "Dublin": (-6.2603, 53.3498),
    "Copenhagen": (12.5683, 55.6761),
    "Stockholm": (18.0686, 59.3293),
    "Warsaw": (21.0122, 52.2297),
}

# Extract data
names = list(cities.keys())
lons = np.array([cities[c][0] for c in names])
lats = np.array([cities[c][1] for c in names])

# Visitor counts (millions per year) - realistic estimates
visitors = np.array([19.1, 21.0, 10.1, 12.0, 8.0, 6.1, 8.0, 7.7, 7.5, 4.5, 4.0, 5.5, 3.5, 4.0, 3.0])


# Convert lon/lat to Web Mercator projection (required for tile maps)
def lonlat_to_mercator(lon, lat):
    """Convert longitude/latitude to Web Mercator coordinates."""
    k = 6378137  # Earth radius in meters
    x = lon * (k * np.pi / 180.0)
    y = np.log(np.tan((90 + lat) * np.pi / 360.0)) * k
    return x, y


x_merc, y_merc = lonlat_to_mercator(lons, lats)

# Create data source
source = ColumnDataSource(
    data={
        "x": x_merc,
        "y": y_merc,
        "lon": lons,
        "lat": lats,
        "name": names,
        "visitors": visitors,
        "size": visitors * 2.0 + 25,  # Scale size by visitors
    }
)

# Create figure with Web Mercator projection
p = figure(
    width=4800,
    height=2700,
    x_axis_type="mercator",
    y_axis_type="mercator",
    title="map-tile-background · bokeh · pyplots.ai",
    tools="pan,wheel_zoom,box_zoom,reset",
    active_scroll="wheel_zoom",
)

# Add tile background (CartoDB Positron for clean look)
p.add_tile(xyz.CartoDB.Positron)

# Plot city markers with color based on visitor count
p.scatter("x", "y", source=source, size="size", fill_color="#306998", fill_alpha=0.7, line_color="white", line_width=3)

# Add hover tool
hover = HoverTool(
    tooltips=[("City", "@name"), ("Visitors", "@visitors{0.0}M/year"), ("Location", "@lat{0.00}°N, @lon{0.00}°E")]
)
p.add_tools(hover)

# Styling for large canvas
p.title.text_font_size = "32pt"
p.title.align = "center"

# Axis labels
p.xaxis.axis_label = "Longitude"
p.yaxis.axis_label = "Latitude"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "16pt"
p.yaxis.major_label_text_font_size = "16pt"

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

# Save as PNG
export_png(p, filename="plot.png")

# Also save as HTML for interactivity
output_file("plot.html")
save(p)
