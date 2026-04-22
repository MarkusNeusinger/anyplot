""" pyplots.ai
scatter-map-geographic: Scatter Map with Geographic Points
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColorBar, ColumnDataSource, LinearColorMapper, WMTSTileSource
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Major cities with population and elevation
np.random.seed(42)
cities = {
    "name": [
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Phoenix",
        "Philadelphia",
        "San Antonio",
        "San Diego",
        "Dallas",
        "San Jose",
        "London",
        "Paris",
        "Berlin",
        "Madrid",
        "Rome",
        "Tokyo",
        "Beijing",
        "Shanghai",
        "Mumbai",
        "Sydney",
        "São Paulo",
        "Mexico City",
        "Cairo",
        "Lagos",
        "Johannesburg",
        "Toronto",
        "Vancouver",
        "Montreal",
        "Buenos Aires",
        "Lima",
    ],
    "lat": [
        40.71,
        34.05,
        41.88,
        29.76,
        33.45,
        39.95,
        29.42,
        32.72,
        32.78,
        37.34,
        51.51,
        48.86,
        52.52,
        40.42,
        41.90,
        35.68,
        39.90,
        31.23,
        19.08,
        -33.87,
        -23.55,
        19.43,
        30.04,
        6.52,
        -26.20,
        43.65,
        49.28,
        45.50,
        -34.60,
        -12.05,
    ],
    "lon": [
        -74.01,
        -118.24,
        -87.63,
        -95.37,
        -112.07,
        -75.17,
        -98.49,
        -117.16,
        -96.80,
        -121.89,
        -0.13,
        2.35,
        13.40,
        -3.70,
        12.50,
        139.69,
        116.41,
        121.47,
        72.88,
        151.21,
        -46.63,
        -99.13,
        31.24,
        3.38,
        28.04,
        -79.38,
        -123.12,
        -73.57,
        -58.38,
        -77.03,
    ],
    "population": [
        8.3,
        3.9,
        2.7,
        2.3,
        1.6,
        1.6,
        1.5,
        1.4,
        1.3,
        1.0,
        8.9,
        2.2,
        3.6,
        3.2,
        2.9,
        13.9,
        21.5,
        24.9,
        20.7,
        5.3,
        12.3,
        8.9,
        10.2,
        15.4,
        5.8,
        2.9,
        0.7,
        1.8,
        3.1,
        10.5,
    ],
    "elevation": [
        10,
        71,
        182,
        15,
        340,
        12,
        198,
        19,
        131,
        25,
        11,
        35,
        34,
        657,
        21,
        40,
        55,
        4,
        14,
        58,
        760,
        2240,
        75,
        41,
        1753,
        76,
        0,
        47,
        25,
        154,
    ],
}


# Convert lat/lon to Web Mercator projection (required for tile maps)
def lat_lon_to_mercator(lat, lon):
    """Convert latitude/longitude to Web Mercator (EPSG:3857) coordinates."""
    k = 6378137  # Earth radius in meters
    x = lon * (k * np.pi / 180.0)
    y = np.log(np.tan((90 + lat) * np.pi / 360.0)) * k
    return x, y


lats = np.array(cities["lat"])
lons = np.array(cities["lon"])
mercator_x, mercator_y = lat_lon_to_mercator(lats, lons)

# Normalize size based on population (scaled for visibility on large canvas)
populations = np.array(cities["population"])
sizes = 25 + (populations / populations.max()) * 55  # Range: 25-80 for 4800x2700

# Create color mapper for elevation
elevations = np.array(cities["elevation"])
color_mapper = LinearColorMapper(palette="Viridis256", low=elevations.min(), high=elevations.max())

# Create data source
source = ColumnDataSource(
    data={
        "x": mercator_x,
        "y": mercator_y,
        "name": cities["name"],
        "lat": lats,
        "lon": lons,
        "population": populations,
        "elevation": elevations,
        "size": sizes,
    }
)

# Create figure with tile map
p = figure(
    width=4800,
    height=2700,
    x_axis_type="mercator",
    y_axis_type="mercator",
    title="World Cities · scatter-map-geographic · bokeh · pyplots.ai",
    tools="pan,wheel_zoom,box_zoom,reset,hover,save",
    tooltips=[
        ("City", "@name"),
        ("Population", "@population{0.0} million"),
        ("Elevation", "@elevation m"),
        ("Coordinates", "(@lat, @lon)"),
    ],
)

# Add map tiles (CartoDB Positron for clean basemap)
tile_url = "https://tiles.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
tile_source = WMTSTileSource(url=tile_url)
p.add_tile(tile_source)

# Add scatter points
p.scatter(
    x="x",
    y="y",
    source=source,
    size="size",
    fill_color={"field": "elevation", "transform": color_mapper},
    fill_alpha=0.75,
    line_color="#306998",
    line_width=2.5,
)

# Add color bar for elevation
color_bar = ColorBar(
    color_mapper=color_mapper,
    title="Elevation (m)",
    title_text_font_size="22pt",
    major_label_text_font_size="18pt",
    label_standoff=15,
    border_line_color=None,
    location=(0, 0),
    width=40,
    height=600,
    margin=20,
)
p.add_layout(color_bar, "right")

# Styling
p.title.text_font_size = "32pt"
p.title.text_color = "#306998"
p.xaxis.axis_label = "Longitude"
p.yaxis.axis_label = "Latitude"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Set view to show entire world
p.x_range.start = -15000000
p.x_range.end = 18000000
p.y_range.start = -6000000
p.y_range.end = 8500000

# Background and border
p.background_fill_color = None
p.border_fill_color = "#ffffff"
p.outline_line_color = "#306998"
p.outline_line_width = 2

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="World Cities · scatter-map-geographic · bokeh", resources=CDN)
