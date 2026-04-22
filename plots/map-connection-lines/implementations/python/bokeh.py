""" pyplots.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure


# Data: Major international flight routes between airports
# Airport coordinates (lat, lon)
airports = {
    "JFK": (40.6413, -73.7781),  # New York
    "LHR": (51.4700, -0.4543),  # London
    "CDG": (49.0097, 2.5479),  # Paris
    "DXB": (25.2532, 55.3657),  # Dubai
    "SIN": (1.3644, 103.9915),  # Singapore
    "HND": (35.5494, 139.7798),  # Tokyo
    "SYD": (-33.9399, 151.1753),  # Sydney
    "LAX": (33.9416, -118.4085),  # Los Angeles
    "SFO": (37.6213, -122.3790),  # San Francisco
    "ORD": (41.9742, -87.9073),  # Chicago
    "FRA": (50.0379, 8.5622),  # Frankfurt
    "AMS": (52.3105, 4.7683),  # Amsterdam
}

# Flight connections with passenger volume (in millions annually)
routes = [
    ("JFK", "LHR", 4.5),
    ("JFK", "CDG", 2.8),
    ("LAX", "HND", 3.2),
    ("SFO", "SIN", 1.5),
    ("LHR", "DXB", 3.8),
    ("CDG", "DXB", 2.1),
    ("DXB", "SIN", 2.5),
    ("SIN", "SYD", 2.9),
    ("LHR", "SYD", 1.2),
    ("JFK", "FRA", 2.3),
    ("ORD", "LHR", 1.8),
    ("LAX", "SYD", 1.6),
    ("FRA", "SIN", 1.4),
    ("AMS", "HND", 0.9),
    ("CDG", "HND", 1.1),
]

# Prepare data for connection lines
line_xs = []
line_ys = []
line_widths = []
line_alphas = []
route_labels = []
passenger_volumes = []

# Scale passenger volume to line widths
volumes = [r[2] for r in routes]
min_vol, max_vol = min(volumes), max(volumes)

for origin, dest, volume in routes:
    o_lat, o_lon = airports[origin]
    d_lat, d_lon = airports[dest]

    # Generate curved arc points (inlined for KISS compliance)
    num_points = 50
    t = np.linspace(0, 1, num_points)

    # Linear interpolation for base path
    arc_lons = o_lon + (d_lon - o_lon) * t
    arc_lats = o_lat + (d_lat - o_lat) * t

    # Add curvature: calculate perpendicular offset based on distance
    dist = np.sqrt((d_lon - o_lon) ** 2 + (d_lat - o_lat) ** 2)
    mid_offset = dist * 0.15  # 15% of distance as max curve height

    # Parabolic curve for the offset
    curve = 4 * t * (1 - t) * mid_offset

    # Calculate perpendicular direction (rotate 90 degrees)
    dx = d_lon - o_lon
    dy = d_lat - o_lat
    length = np.sqrt(dx**2 + dy**2)
    if length > 0:
        perp_x = -dy / length
        perp_y = dx / length
    else:
        perp_x, perp_y = 0, 0

    # Apply curve offset perpendicular to the line
    arc_lons = arc_lons + perp_x * curve
    arc_lats = arc_lats + perp_y * curve

    line_xs.append(arc_lons.tolist())
    line_ys.append(arc_lats.tolist())

    # Scale line width based on volume (3 to 12 pixels)
    normalized = (volume - min_vol) / (max_vol - min_vol) if max_vol > min_vol else 0.5
    line_widths.append(3 + normalized * 9)
    line_alphas.append(0.4 + normalized * 0.3)

    # Store route info for hover tooltips
    route_labels.append(f"{origin} → {dest}")
    passenger_volumes.append(f"{volume}M passengers/year")

# Prepare airport markers data
airport_names = list(airports.keys())
airport_lons = [airports[a][1] for a in airport_names]
airport_lats = [airports[a][0] for a in airport_names]

# Create sources
line_source = ColumnDataSource(
    data={
        "xs": line_xs,
        "ys": line_ys,
        "line_width": line_widths,
        "alpha": line_alphas,
        "route": route_labels,
        "passengers": passenger_volumes,
    }
)

airport_source = ColumnDataSource(data={"x": airport_lons, "y": airport_lats, "name": airport_names})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="map-connection-lines · bokeh · pyplots.ai",
    x_axis_label="Longitude (degrees)",
    y_axis_label="Latitude (degrees)",
    x_range=(-180, 180),
    y_range=(-60, 80),
    tools="pan,wheel_zoom,box_zoom,reset",
)

# Style the figure
p.title.text_font_size = "32pt"
p.title.text_color = "#333333"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Background styling
p.background_fill_color = "#f5f5f5"
p.border_fill_color = "white"
p.grid.grid_line_color = "#cccccc"
p.grid.grid_line_alpha = 0.5
p.grid.grid_line_dash = [6, 4]

# Draw connection lines (Python Blue color)
lines_renderer = p.multi_line(
    xs="xs",
    ys="ys",
    source=line_source,
    line_width="line_width",
    line_alpha="alpha",
    line_color="#306998",
    line_cap="round",
)

# Add HoverTool for route information
hover = HoverTool(
    renderers=[lines_renderer], tooltips=[("Route", "@route"), ("Traffic", "@passengers")], line_policy="interp"
)
p.add_tools(hover)

# Draw airport markers (Python Yellow)
p.scatter(x="x", y="y", source=airport_source, size=20, color="#FFD43B", line_color="#306998", line_width=3, alpha=0.9)

# Add airport labels with offset to reduce overlap
p.text(
    x="x",
    y="y",
    text="name",
    source=airport_source,
    x_offset=12,
    y_offset=8,
    text_font_size="14pt",
    text_color="#333333",
    text_font_style="bold",
)

# Create legend items to explain line thickness
# Draw example lines for the legend
legend_source_thin = ColumnDataSource(data={"xs": [[-170, -150]], "ys": [[70, 70]]})
legend_source_medium = ColumnDataSource(data={"xs": [[-170, -150]], "ys": [[62, 62]]})
legend_source_thick = ColumnDataSource(data={"xs": [[-170, -150]], "ys": [[54, 54]]})

thin_line = p.multi_line(
    xs="xs", ys="ys", source=legend_source_thin, line_width=3, line_color="#306998", line_alpha=0.4
)
medium_line = p.multi_line(
    xs="xs", ys="ys", source=legend_source_medium, line_width=7.5, line_color="#306998", line_alpha=0.55
)
thick_line = p.multi_line(
    xs="xs", ys="ys", source=legend_source_thick, line_width=12, line_color="#306998", line_alpha=0.7
)

# Add text labels for the legend
p.text(
    x=[-145], y=[70], text=["Low traffic (~1M/yr)"], text_font_size="16pt", text_color="#333333", text_baseline="middle"
)
p.text(
    x=[-145],
    y=[62],
    text=["Medium traffic (~2.5M/yr)"],
    text_font_size="16pt",
    text_color="#333333",
    text_baseline="middle",
)
p.text(
    x=[-145],
    y=[54],
    text=["High traffic (~4.5M/yr)"],
    text_font_size="16pt",
    text_color="#333333",
    text_baseline="middle",
)

# Add legend title
p.text(x=[-170], y=[78], text=["Passenger Volume"], text_font_size="18pt", text_color="#333333", text_font_style="bold")

# Save outputs
export_png(p, filename="plot.png")

# Also save HTML for interactivity
output_file("plot.html")
save(p)
