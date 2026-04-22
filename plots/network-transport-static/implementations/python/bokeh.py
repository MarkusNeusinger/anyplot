""" pyplots.ai
network-transport-static: Static Transport Network Diagram
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-10
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Arrow, ColumnDataSource, Label, LabelSet, VeeHead
from bokeh.plotting import figure
from bokeh.resources import CDN


np.random.seed(42)

# Data: Regional rail network with stations and routes
# Scaled coordinates for 4800x2700 canvas with margins
stations = [
    {"id": "A", "label": "Central Station", "x": 500, "y": 1350},
    {"id": "B", "label": "North Terminal", "x": 1100, "y": 2100},
    {"id": "C", "label": "East Junction", "x": 1900, "y": 1350},
    {"id": "D", "label": "South Hub", "x": 1100, "y": 600},
    {"id": "E", "label": "Airport", "x": 2700, "y": 1900},
    {"id": "F", "label": "University", "x": 2700, "y": 800},
    {"id": "G", "label": "Industrial Park", "x": 3600, "y": 1350},
    {"id": "H", "label": "Harbor", "x": 700, "y": 2300},
    {"id": "I", "label": "Stadium", "x": 700, "y": 400},
    {"id": "J", "label": "Tech Campus", "x": 3200, "y": 2100},
    {"id": "K", "label": "Medical Center", "x": 3200, "y": 600},
    {"id": "L", "label": "Downtown", "x": 2300, "y": 1350},
]

station_lookup = {s["id"]: s for s in stations}

# Routes: Train services with departure and arrival times
routes = [
    {"source_id": "A", "target_id": "B", "route_id": "RE 10", "departure_time": "06:00", "arrival_time": "06:25"},
    {"source_id": "A", "target_id": "D", "route_id": "RE 20", "departure_time": "06:15", "arrival_time": "06:35"},
    {"source_id": "A", "target_id": "C", "route_id": "RE 30", "departure_time": "06:30", "arrival_time": "07:00"},
    {"source_id": "B", "target_id": "H", "route_id": "S1", "departure_time": "06:35", "arrival_time": "06:50"},
    {"source_id": "B", "target_id": "E", "route_id": "RE 10", "departure_time": "06:40", "arrival_time": "07:15"},
    {"source_id": "C", "target_id": "L", "route_id": "RE 30", "departure_time": "07:05", "arrival_time": "07:20"},
    {"source_id": "C", "target_id": "F", "route_id": "RE 40", "departure_time": "07:10", "arrival_time": "07:35"},
    {"source_id": "D", "target_id": "I", "route_id": "S2", "departure_time": "06:45", "arrival_time": "07:00"},
    {"source_id": "D", "target_id": "F", "route_id": "RE 20", "departure_time": "06:50", "arrival_time": "07:25"},
    {"source_id": "E", "target_id": "J", "route_id": "RE 10", "departure_time": "07:25", "arrival_time": "07:40"},
    {"source_id": "F", "target_id": "G", "route_id": "RE 40", "departure_time": "07:45", "arrival_time": "08:10"},
    {"source_id": "F", "target_id": "K", "route_id": "RE 20", "departure_time": "07:35", "arrival_time": "07:55"},
    {"source_id": "L", "target_id": "E", "route_id": "EX 1", "departure_time": "07:30", "arrival_time": "07:50"},
    {"source_id": "L", "target_id": "G", "route_id": "RE 30", "departure_time": "07:25", "arrival_time": "08:00"},
    {"source_id": "J", "target_id": "G", "route_id": "RE 10", "departure_time": "07:50", "arrival_time": "08:15"},
    {"source_id": "K", "target_id": "G", "route_id": "RE 20", "departure_time": "08:05", "arrival_time": "08:25"},
    {"source_id": "A", "target_id": "L", "route_id": "EX 1", "departure_time": "07:00", "arrival_time": "07:20"},
    {"source_id": "H", "target_id": "A", "route_id": "S1", "departure_time": "05:30", "arrival_time": "05:55"},
    {"source_id": "I", "target_id": "A", "route_id": "S2", "departure_time": "05:45", "arrival_time": "06:10"},
]

# Route colors by type
route_colors = {
    "RE 10": "#306998",  # Python Blue - Regional Express
    "RE 20": "#4A90D9",  # Light Blue - Regional Express
    "RE 30": "#2E7D32",  # Green - Regional Express
    "RE 40": "#7B1FA2",  # Purple - Regional Express
    "S1": "#FFD43B",  # Python Yellow - S-Bahn
    "S2": "#FFA726",  # Orange - S-Bahn
    "EX 1": "#C62828",  # Red - Express
}

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="network-transport-static · bokeh · pyplots.ai",
    x_range=(100, 4100),
    y_range=(100, 2550),
    tools="",
    toolbar_location=None,
)

# Style the figure - scaled for 4800x2700 canvas
p.title.text_font_size = "48pt"
p.title.align = "center"
p.xgrid.visible = False
p.ygrid.visible = False
p.xaxis.visible = False
p.yaxis.visible = False
p.outline_line_color = None
p.background_fill_color = "#FAFAFA"
p.min_border_left = 80
p.min_border_right = 80
p.min_border_top = 100
p.min_border_bottom = 80

# Draw routes as arrows with labels
for route in routes:
    src = station_lookup[route["source_id"]]
    tgt = station_lookup[route["target_id"]]

    # Calculate direction vector
    dx = tgt["x"] - src["x"]
    dy = tgt["y"] - src["y"]
    length = np.sqrt(dx**2 + dy**2)

    # Normalize direction
    if length > 0:
        nx, ny = dx / length, dy / length
    else:
        nx, ny = 0, 0

    # Offset for multiple routes between same stations (perpendicular offset)
    # Find how many routes share this pair
    pair_key = tuple(sorted([route["source_id"], route["target_id"]]))
    same_pair_routes = [r for r in routes if tuple(sorted([r["source_id"], r["target_id"]])) == pair_key]
    pair_index = same_pair_routes.index(route)
    num_routes = len(same_pair_routes)

    # Perpendicular vector
    perp_x, perp_y = -ny, nx
    offset_amount = (pair_index - (num_routes - 1) / 2) * 80

    # Start and end points with offset and shortened to not overlap nodes
    node_radius = 120
    start_x = src["x"] + nx * node_radius + perp_x * offset_amount
    start_y = src["y"] + ny * node_radius + perp_y * offset_amount
    end_x = tgt["x"] - nx * node_radius + perp_x * offset_amount
    end_y = tgt["y"] - ny * node_radius + perp_y * offset_amount

    color = route_colors.get(route["route_id"], "#666666")

    # Draw arrow - scaled for large canvas
    p.add_layout(
        Arrow(
            end=VeeHead(size=35, fill_color=color, line_color=color),
            x_start=start_x,
            y_start=start_y,
            x_end=end_x,
            y_end=end_y,
            line_color=color,
            line_width=6,
            line_alpha=0.85,
        )
    )

    # Route label at midpoint
    mid_x = (start_x + end_x) / 2 + perp_x * 40
    mid_y = (start_y + end_y) / 2 + perp_y * 40

    label_text = f"{route['route_id']} | {route['departure_time']}→{route['arrival_time']}"

    # Calculate angle for label rotation
    angle = np.arctan2(dy, dx)
    if angle > np.pi / 2:
        angle -= np.pi
    elif angle < -np.pi / 2:
        angle += np.pi

    p.add_layout(
        Label(
            x=mid_x,
            y=mid_y,
            text=label_text,
            text_font_size="18pt",
            text_color=color,
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
            angle=angle,
            background_fill_color="white",
            background_fill_alpha=0.9,
        )
    )

# Draw station nodes
station_x = [s["x"] for s in stations]
station_y = [s["y"] for s in stations]
station_labels = [s["label"] for s in stations]

station_source = ColumnDataSource(data={"x": station_x, "y": station_y, "label": station_labels})

# Draw station circles - larger for visibility
p.scatter(x="x", y="y", source=station_source, size=100, fill_color="white", line_color="#306998", line_width=6)

# Station labels - positioned below nodes for clarity
labels = LabelSet(
    x="x",
    y="y",
    text="label",
    source=station_source,
    text_font_size="18pt",
    text_font_style="bold",
    text_color="#333333",
    text_align="center",
    text_baseline="top",
    y_offset=-70,
)
p.add_layout(labels)

# Add legend - positioned and scaled for large canvas
legend_x = 3750
legend_y = 2400
legend_items = [("Regional Express (RE)", "#306998"), ("S-Bahn Local (S)", "#FFD43B"), ("Express (EX)", "#C62828")]

for i, (label, color) in enumerate(legend_items):
    y_pos = legend_y - i * 150
    p.scatter(x=[legend_x], y=[y_pos], size=40, fill_color=color, line_color=color)
    p.add_layout(
        Label(x=legend_x + 70, y=y_pos, text=label, text_font_size="24pt", text_color="#333333", text_baseline="middle")
    )

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Regional Rail Network")
