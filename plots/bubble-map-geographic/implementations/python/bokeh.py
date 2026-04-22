""" pyplots.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, LabelSet, Legend, LegendItem, WMTSTileSource
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - World cities with population (in millions)
np.random.seed(42)
cities = {
    "name": [
        "Tokyo",
        "Delhi",
        "Shanghai",
        "São Paulo",
        "Mexico City",
        "Cairo",
        "Mumbai",
        "Beijing",
        "Dhaka",
        "Osaka",
        "New York",
        "Karachi",
        "Buenos Aires",
        "Istanbul",
        "Lagos",
        "London",
        "Paris",
        "Bangkok",
        "Lima",
        "Sydney",
        "Toronto",
        "Singapore",
        "Berlin",
        "Madrid",
        "Johannesburg",
    ],
    "lat": [
        35.68,
        28.61,
        31.23,
        -23.55,
        19.43,
        30.04,
        19.08,
        39.90,
        23.81,
        34.69,
        40.71,
        24.86,
        -34.60,
        41.01,
        6.52,
        51.51,
        48.86,
        13.76,
        -12.05,
        -33.87,
        43.65,
        1.35,
        52.52,
        40.42,
        -26.20,
    ],
    "lon": [
        139.69,
        77.21,
        121.47,
        -46.63,
        -99.13,
        31.24,
        72.88,
        116.41,
        90.41,
        135.50,
        -74.01,
        67.01,
        -58.38,
        28.98,
        3.38,
        -0.13,
        2.35,
        100.50,
        -77.03,
        151.21,
        -79.38,
        103.82,
        13.40,
        -3.70,
        28.04,
    ],
    # Population in millions (2024 estimates)
    "population": [
        37.4,
        32.9,
        28.5,
        22.4,
        21.8,
        21.3,
        20.7,
        20.5,
        22.5,
        19.1,
        18.9,
        16.5,
        15.5,
        15.6,
        15.4,
        9.5,
        11.1,
        10.7,
        10.9,
        5.3,
        6.2,
        5.9,
        3.6,
        6.7,
        5.8,
    ],
    # Region for color grouping
    "region": [
        "Asia",
        "Asia",
        "Asia",
        "Americas",
        "Americas",
        "Africa",
        "Asia",
        "Asia",
        "Asia",
        "Asia",
        "Americas",
        "Asia",
        "Americas",
        "Europe",
        "Africa",
        "Europe",
        "Europe",
        "Asia",
        "Americas",
        "Oceania",
        "Americas",
        "Asia",
        "Europe",
        "Europe",
        "Africa",
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

# Population data
populations = np.array(cities["population"])

# Scale bubble area proportionally to population (not radius)
# Using sqrt to make area proportional to value
min_size = 20
max_size = 90
pop_normalized = (populations - populations.min()) / (populations.max() - populations.min())
sizes = min_size + np.sqrt(pop_normalized) * (max_size - min_size)

# Color mapping by region
region_colors = {
    "Asia": "#306998",  # Python Blue
    "Americas": "#FFD43B",  # Python Yellow
    "Europe": "#4B8BBE",  # Light Blue
    "Africa": "#9B59B6",  # Purple
    "Oceania": "#27AE60",  # Green
}
colors = [region_colors[r] for r in cities["region"]]

# Create data source
source = ColumnDataSource(
    data={
        "x": mercator_x,
        "y": mercator_y,
        "name": cities["name"],
        "lat": lats,
        "lon": lons,
        "population": populations,
        "region": cities["region"],
        "size": sizes,
        "color": colors,
    }
)

# Create figure with tile map
p = figure(
    width=4800,
    height=2700,
    x_axis_type="mercator",
    y_axis_type="mercator",
    title="World Cities by Population · bubble-map-geographic · bokeh · pyplots.ai",
    tools="pan,wheel_zoom,box_zoom,reset,hover,save",
    tooltips=[
        ("City", "@name"),
        ("Population", "@population{0.0} million"),
        ("Region", "@region"),
        ("Coordinates", "(@lat, @lon)"),
    ],
)

# Add map tiles (CartoDB Positron for clean basemap)
tile_url = "https://tiles.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
tile_source = WMTSTileSource(url=tile_url)
p.add_tile(tile_source)

# Create separate renderers for each region to build legend
legend_items = []
for region, color in region_colors.items():
    region_mask = [r == region for r in cities["region"]]
    if any(region_mask):
        region_source = ColumnDataSource(
            data={"x": mercator_x[region_mask], "y": mercator_y[region_mask], "size": sizes[region_mask]}
        )
        renderer = p.scatter(
            x="x",
            y="y",
            source=region_source,
            size="size",
            fill_color=color,
            fill_alpha=0.6,
            line_color="#333333",
            line_width=2,
        )
        legend_items.append(LegendItem(label=region, renderers=[renderer]))

# Add legend for regions
legend = Legend(
    items=legend_items,
    location="top_left",
    title="Region",
    title_text_font_size="24pt",
    label_text_font_size="20pt",
    glyph_height=40,
    glyph_width=40,
    spacing=15,
    padding=20,
    background_fill_alpha=0.85,
    background_fill_color="white",
    border_line_color="#306998",
    border_line_width=2,
)
p.add_layout(legend, "right")

# Add size legend using reference bubbles (manual annotation)
# Create reference points for size legend (placed off-map area)
size_legend_pops = [5, 15, 25, 35]  # Reference populations in millions
size_legend_x = 19500000  # Position to the right of the map
size_legend_y_start = 6000000
size_legend_y_spacing = 1800000

# Calculate sizes for legend bubbles
size_legend_sizes = []
for pop in size_legend_pops:
    pop_norm = (pop - populations.min()) / (populations.max() - populations.min())
    size_legend_sizes.append(min_size + np.sqrt(pop_norm) * (max_size - min_size))

size_legend_source = ColumnDataSource(
    data={
        "x": [size_legend_x] * len(size_legend_pops),
        "y": [size_legend_y_start - i * size_legend_y_spacing for i in range(len(size_legend_pops))],
        "size": size_legend_sizes,
        "label": [f"{p}M" for p in size_legend_pops],
    }
)

p.scatter(
    x="x",
    y="y",
    source=size_legend_source,
    size="size",
    fill_color="#306998",
    fill_alpha=0.6,
    line_color="#333333",
    line_width=2,
)

# Add labels for size legend
labels = LabelSet(
    x="x",
    y="y",
    text="label",
    source=size_legend_source,
    x_offset=60,
    y_offset=-10,
    text_font_size="18pt",
    text_color="#333333",
    text_align="left",
)
p.add_layout(labels)

# Add "Population" title for size legend
p.text(
    x=[size_legend_x - 100000],
    y=[size_legend_y_start + 1200000],
    text=["Population"],
    text_font_size="22pt",
    text_font_style="bold",
    text_color="#333333",
)

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

# Set view to show world with space for legends
p.x_range.start = -15000000
p.x_range.end = 22000000
p.y_range.start = -6000000
p.y_range.end = 8500000

# Background and border
p.background_fill_color = None
p.border_fill_color = "#ffffff"
p.outline_line_color = "#306998"
p.outline_line_width = 2

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="World Cities by Population · bubble-map-geographic · bokeh", resources=CDN)
