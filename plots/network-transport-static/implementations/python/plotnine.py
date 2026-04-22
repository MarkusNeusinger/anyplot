""" pyplots.ai
network-transport-static: Static Transport Network Diagram
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-10
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    arrow,
    element_blank,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_void,
)


np.random.seed(42)

# Station data - regional rail network
stations = pd.DataFrame(
    {
        "id": ["CTR", "NTH", "STH", "EST", "WST", "NE", "NW", "SE", "SW", "AIR", "UNI", "IND"],
        "label": [
            "Central",
            "North",
            "South",
            "East",
            "West",
            "Northeast",
            "Northwest",
            "Southeast",
            "Southwest",
            "Airport",
            "University",
            "Industrial",
        ],
        "x": [0.5, 0.5, 0.5, 0.85, 0.15, 0.75, 0.25, 0.75, 0.25, 0.95, 0.05, 0.5],
        "y": [0.5, 0.85, 0.15, 0.5, 0.5, 0.75, 0.75, 0.25, 0.25, 0.65, 0.65, 0.0],
    }
)

# Route data - train services with times
routes_data = [
    # Express routes (RE)
    ("CTR", "NTH", "RE1", "06:00", "06:25"),
    ("NTH", "CTR", "RE1", "06:30", "06:55"),
    ("CTR", "STH", "RE2", "06:15", "06:40"),
    ("STH", "CTR", "RE2", "06:45", "07:10"),
    ("CTR", "EST", "RE3", "07:00", "07:20"),
    ("EST", "CTR", "RE3", "07:30", "07:50"),
    ("CTR", "WST", "RE4", "07:15", "07:35"),
    ("WST", "CTR", "RE4", "07:45", "08:05"),
    # Regional routes (RB)
    ("NTH", "NE", "RB1", "08:00", "08:15"),
    ("NE", "EST", "RB1", "08:20", "08:40"),
    ("NTH", "NW", "RB2", "08:00", "08:15"),
    ("NW", "WST", "RB2", "08:20", "08:40"),
    ("STH", "SE", "RB3", "08:00", "08:15"),
    ("SE", "EST", "RB3", "08:20", "08:40"),
    ("STH", "SW", "RB4", "08:00", "08:15"),
    ("SW", "WST", "RB4", "08:20", "08:40"),
    # Airport Express (AE)
    ("CTR", "EST", "AE1", "09:00", "09:15"),
    ("EST", "AIR", "AE1", "09:20", "09:35"),
    ("AIR", "EST", "AE1", "10:00", "10:15"),
    ("EST", "CTR", "AE1", "10:20", "10:35"),
    # Local routes (S)
    ("CTR", "UNI", "S1", "08:30", "08:50"),
    ("UNI", "NW", "S1", "08:55", "09:10"),
    ("CTR", "IND", "S2", "09:00", "09:25"),
    ("IND", "STH", "S2", "09:30", "09:45"),
]

routes = pd.DataFrame(routes_data, columns=["source", "target", "route_id", "dep", "arr"])

# Create station lookup
station_coords = stations.set_index("id")[["x", "y"]]

# Add coordinates to routes
routes["x"] = routes["source"].map(station_coords["x"])
routes["y"] = routes["source"].map(station_coords["y"])
routes["xend"] = routes["target"].map(station_coords["x"])
routes["yend"] = routes["target"].map(station_coords["y"])

# Route type for coloring
routes["route_type"] = routes["route_id"].str.extract(r"([A-Z]+)")[0]

# Offset overlapping routes - larger offset to separate labels
route_pairs = routes.groupby(["source", "target"]).cumcount()
offset_amount = 0.025

# Calculate perpendicular offset for multiple routes
dx = routes["xend"] - routes["x"]
dy = routes["yend"] - routes["y"]
length = np.sqrt(dx**2 + dy**2)
perpx = -dy / length * offset_amount * route_pairs
perpy = dx / length * offset_amount * route_pairs

routes["x"] = routes["x"] + perpx
routes["y"] = routes["y"] + perpy
routes["xend"] = routes["xend"] + perpx
routes["yend"] = routes["yend"] + perpy

# Shorten edges so arrows don't overlap with nodes
shorten = 0.04
dx = routes["xend"] - routes["x"]
dy = routes["yend"] - routes["y"]
length = np.sqrt(dx**2 + dy**2)
routes["x"] = routes["x"] + dx / length * shorten
routes["y"] = routes["y"] + dy / length * shorten
routes["xend"] = routes["xend"] - dx / length * shorten
routes["yend"] = routes["yend"] - dy / length * shorten

# Calculate edge label positions - stagger along edge to reduce overlaps
# Use 40%-60% position alternating based on index to spread labels
label_offset = np.where(routes.index % 2 == 0, 0.4, 0.6)
routes["label_x"] = routes["x"] + (routes["xend"] - routes["x"]) * label_offset
routes["label_y"] = routes["y"] + (routes["yend"] - routes["y"]) * label_offset
routes["edge_label"] = routes["route_id"] + " | " + routes["dep"] + "→" + routes["arr"]

# Color palette for route types
route_colors = {
    "RE": "#306998",  # Python Blue - Express
    "RB": "#FFD43B",  # Python Yellow - Regional
    "AE": "#E74C3C",  # Red - Airport
    "S": "#27AE60",  # Green - Local
}

# Create the plot
plot = (
    ggplot()
    # Draw route edges with arrows
    + geom_segment(
        data=routes,
        mapping=aes(x="x", y="y", xend="xend", yend="yend", color="route_type"),
        size=1.5,
        arrow=arrow(length=0.15, type="closed", angle=25),
    )
    # Draw station nodes
    + geom_point(data=stations, mapping=aes(x="x", y="y"), size=12, fill="white", color="#306998", stroke=2)
    # Station labels
    + geom_text(
        data=stations,
        mapping=aes(x="x", y="y", label="label"),
        size=12,
        fontweight="bold",
        color="#333333",
        nudge_y=0.06,
    )
    # Edge labels (route and times) - larger size and better positioning
    + geom_text(
        data=routes,
        mapping=aes(x="label_x", y="label_y", label="edge_label", color="route_type"),
        size=8,
        nudge_y=0.04,
        fontweight="bold",
        show_legend=False,
    )
    # Color scale using raw route codes as per spec for legend accuracy
    + scale_color_manual(
        values=route_colors,
        name="Route Type",
        labels={"RE": "RE (Express)", "RB": "RB (Regional)", "AE": "AE (Airport)", "S": "S (Local)"},
        limits=["RE", "RB", "AE", "S"],
    )
    # Labels and theme
    + labs(title="network-transport-static · plotnine · pyplots.ai")
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        legend_position="right",
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_background=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
