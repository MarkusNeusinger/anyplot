""" pyplots.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data: Trade flow between major world ports (fictional but realistic magnitude)
np.random.seed(42)

# Major port cities with coordinates
ports = {
    "Shanghai": (31.2304, 121.4737),
    "Singapore": (1.3521, 103.8198),
    "Rotterdam": (51.9225, 4.4792),
    "Los Angeles": (33.7490, -118.2437),
    "Dubai": (25.2048, 55.2708),
    "Hong Kong": (22.3193, 114.1694),
    "Hamburg": (53.5511, 9.9937),
    "New York": (40.7128, -74.0060),
    "Tokyo": (35.6762, 139.6503),
    "Sydney": (-33.8688, 151.2093),
}

# Generate flow data between ports
flows = []
port_names = list(ports.keys())

# Create meaningful trade flows
flow_pairs = [
    ("Shanghai", "Los Angeles", 850),
    ("Shanghai", "Rotterdam", 720),
    ("Singapore", "Rotterdam", 580),
    ("Singapore", "Dubai", 490),
    ("Hong Kong", "Los Angeles", 620),
    ("Hong Kong", "Hamburg", 410),
    ("Rotterdam", "New York", 530),
    ("Dubai", "Singapore", 380),
    ("Tokyo", "Los Angeles", 560),
    ("Tokyo", "Shanghai", 470),
    ("Shanghai", "Singapore", 650),
    ("Los Angeles", "New York", 420),
    ("Sydney", "Singapore", 340),
    ("Sydney", "Shanghai", 290),
    ("Hamburg", "New York", 310),
    ("Rotterdam", "Dubai", 280),
    ("New York", "Rotterdam", 390),
    ("Dubai", "Hamburg", 260),
]

for origin, dest, flow in flow_pairs:
    origin_lat, origin_lon = ports[origin]
    dest_lat, dest_lon = ports[dest]
    flows.append(
        {
            "origin_name": origin,
            "dest_name": dest,
            "origin_lat": origin_lat,
            "origin_lon": origin_lon,
            "dest_lat": dest_lat,
            "dest_lon": dest_lon,
            "flow": flow,
        }
    )

df = pd.DataFrame(flows)


# Convert lat/lon to Web Mercator projection for tile-based map
def lat_lon_to_mercator(lat, lon):
    """Convert latitude/longitude to Web Mercator coordinates."""
    k = 6378137  # Earth radius in meters
    x = lon * (k * np.pi / 180.0)
    y = np.log(np.tan((90 + lat) * np.pi / 360.0)) * k
    return x, y


# Convert coordinates
df["origin_x"], df["origin_y"] = zip(
    *[lat_lon_to_mercator(lat, lon) for lat, lon in zip(df["origin_lat"], df["origin_lon"], strict=True)], strict=True
)
df["dest_x"], df["dest_y"] = zip(
    *[lat_lon_to_mercator(lat, lon) for lat, lon in zip(df["dest_lat"], df["dest_lon"], strict=True)], strict=True
)


# Generate Bezier curve points for each flow
def bezier_curve(x0, y0, x1, y1, num_points=50):
    """Generate quadratic Bezier curve between two points with control point above midpoint."""
    t = np.linspace(0, 1, num_points)
    # Control point: midpoint with vertical offset proportional to distance
    mid_x = (x0 + x1) / 2
    mid_y = (y0 + y1) / 2
    distance = np.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
    # Curve height: 20% of distance, curving upward (in Mercator coordinates)
    ctrl_y = mid_y + distance * 0.2
    ctrl_x = mid_x
    # Quadratic Bezier
    bx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * ctrl_x + t**2 * x1
    by = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ctrl_y + t**2 * y1
    return bx, by


# Create figure with Web Mercator projection
p = figure(
    width=4800,
    height=2700,
    title="flowmap-origin-destination · bokeh · pyplots.ai",
    x_axis_type="mercator",
    y_axis_type="mercator",
    tools="pan,wheel_zoom,box_zoom,reset",
)

# Add tile provider for basemap (Bokeh 3.x uses string-based tile provider)
p.add_tile("CartoDB Positron")

# Style the title and axes
p.title.text_font_size = "28pt"
p.xaxis.axis_label = "Longitude"
p.yaxis.axis_label = "Latitude"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "16pt"
p.yaxis.major_label_text_font_size = "16pt"

# Normalize flow for line width (scale to 2-12 range)
min_flow = df["flow"].min()
max_flow = df["flow"].max()
df["line_width"] = 2 + (df["flow"] - min_flow) / (max_flow - min_flow) * 10

# Color scale based on flow magnitude (Python Blue to Yellow gradient)
df["color"] = df["flow"].apply(
    lambda f: f"#{int(48 + (255 - 48) * (f - min_flow) / (max_flow - min_flow)):02x}"
    f"{int(105 + (212 - 105) * (f - min_flow) / (max_flow - min_flow)):02x}"
    f"{int(152 + (59 - 152) * (f - min_flow) / (max_flow - min_flow)):02x}"
)

# Draw curved arcs for each flow
for _, row in df.iterrows():
    curve_x, curve_y = bezier_curve(row["origin_x"], row["origin_y"], row["dest_x"], row["dest_y"])

    # Create source for this arc with hover data
    arc_source = ColumnDataSource(
        data={
            "x": curve_x,
            "y": curve_y,
            "origin": [row["origin_name"]] * len(curve_x),
            "dest": [row["dest_name"]] * len(curve_x),
            "flow": [row["flow"]] * len(curve_x),
        }
    )

    p.line(
        x="x",
        y="y",
        source=arc_source,
        line_width=row["line_width"],
        line_color=row["color"],
        line_alpha=0.6,
        line_cap="round",
    )

# Add origin/destination points
port_data = []
for name, (lat, lon) in ports.items():
    x, y = lat_lon_to_mercator(lat, lon)
    port_data.append({"name": name, "x": x, "y": y, "lat": lat, "lon": lon})

port_df = pd.DataFrame(port_data)
port_source = ColumnDataSource(port_df)

# Draw port markers
p.scatter(x="x", y="y", source=port_source, size=20, color="#306998", alpha=0.9, legend_label="Ports")

# Add hover tool for ports
hover_ports = HoverTool(
    tooltips=[("Port", "@name"), ("Latitude", "@lat{0.00}"), ("Longitude", "@lon{0.00}")], renderers=[p.renderers[-1]]
)
p.add_tools(hover_ports)

# Legend styling
p.legend.location = "top_left"
p.legend.label_text_font_size = "18pt"
p.legend.background_fill_alpha = 0.8

# Save outputs
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="Origin-Destination Flow Map", resources=CDN)
