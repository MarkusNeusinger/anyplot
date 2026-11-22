""" anyplot.ai
network-transport-static: Static Transport Network Diagram
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 78/100 | Updated: 2026-11-22
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    arrow,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NODE_CLEARANCE = 0.045  # edges stop this far from a station centre so arrowheads stay visible
PARALLEL_SPACING = 0.05  # perpendicular gap between routes that share a station pair
LABEL_OFFSET = 0.055  # perpendicular distance from an edge to its label

# Columns: set these to your table's column names
SOURCE = "source_id"  # role: routes
TARGET = "target_id"  # role: extra
ROUTE = "route_id"  # role: extra
DEPARTURE = "departure_time"  # role: extra
ARRIVAL = "arrival_time"  # role: extra
ROUTE_TYPE = "Route Type"  # role: extra
SOURCE_NAME = "source_label"  # role: stations
TARGET_NAME = "target_label"  # role: extra
SOURCE_X = "source_x"  # role: extra
SOURCE_Y = "source_y"  # role: extra
TARGET_X = "target_x"  # role: extra
TARGET_Y = "target_y"  # role: extra

# Data: replace this block with your own edge list, for example df = pd.read_csv("routes.csv")
# One row per route; stations carry schematic x/y coordinates (never laid out by an algorithm)
station_table = {
    "A": ("Central", 0.5, 0.5),
    "B": ("North", 0.5, 0.88),
    "C": ("East", 0.82, 0.5),
    "D": ("South", 0.5, 0.12),
    "E": ("West", 0.18, 0.5),
    "F": ("Airport", 0.82, 0.82),
    "G": ("University", 0.18, 0.82),
    "H": ("Harbor", 0.82, 0.18),
    "I": ("Tech Park", 0.18, 0.18),
    "J": ("Stadium", 0.66, 0.32),
}
route_rows = [
    ("A", "B", "RE1", "06:15", "06:35", "Express"),
    ("A", "C", "RE2", "06:30", "06:55", "Express"),
    ("A", "D", "RE3", "07:00", "07:25", "Express"),
    ("A", "E", "RE4", "07:15", "07:40", "Express"),
    ("B", "F", "RB1", "07:00", "07:20", "Regional"),
    ("B", "G", "RB2", "07:30", "07:55", "Regional"),
    ("C", "F", "RB3", "08:00", "08:25", "Regional"),
    ("C", "H", "RB4", "08:15", "08:40", "Regional"),
    ("D", "H", "RB5", "08:30", "08:55", "Regional"),
    ("D", "I", "RB6", "09:00", "09:30", "Regional"),
    ("E", "G", "RB7", "09:15", "09:40", "Regional"),
    ("E", "I", "RB8", "09:30", "09:55", "Regional"),
    ("C", "J", "S1", "10:00", "10:12", "Local"),
    ("J", "H", "S2", "10:15", "10:30", "Local"),
    ("A", "J", "S3", "10:30", "10:50", "Local"),
    ("A", "C", "RE5", "12:30", "12:55", "Express"),
]
df = pd.DataFrame(route_rows, columns=[SOURCE, TARGET, ROUTE, DEPARTURE, ARRIVAL, ROUTE_TYPE])
df[SOURCE_NAME] = df[SOURCE].map(lambda s: station_table[s][0])
df[TARGET_NAME] = df[TARGET].map(lambda s: station_table[s][0])
df[SOURCE_X] = df[SOURCE].map(lambda s: station_table[s][1])
df[SOURCE_Y] = df[SOURCE].map(lambda s: station_table[s][2])
df[TARGET_X] = df[TARGET].map(lambda s: station_table[s][1])
df[TARGET_Y] = df[TARGET].map(lambda s: station_table[s][2])

# Plot: reads only df and the constants above
route_types = list(df[ROUTE_TYPE].unique())
route_colors = {kind: IMPRINT_PALETTE[i] for i, kind in enumerate(route_types)}

# Stations are the distinct endpoints of the routes, at their given coordinates
ends = [(SOURCE, SOURCE_NAME, SOURCE_X, SOURCE_Y), (TARGET, TARGET_NAME, TARGET_X, TARGET_Y)]
nodes = pd.concat(
    [df[list(cols)].set_axis(["node_id", "node_name", "node_x", "node_y"], axis=1) for cols in ends]
).drop_duplicates("node_id")

edges = df.copy()
dx, dy = edges[TARGET_X] - edges[SOURCE_X], edges[TARGET_Y] - edges[SOURCE_Y]
length = np.hypot(dx, dy)
perp_x, perp_y = -dy / length, dx / length

# Routes sharing a station pair fan out perpendicular to the edge
pair_size = edges.groupby([SOURCE, TARGET])[ROUTE].transform("size")
pair_rank = edges.groupby([SOURCE, TARGET]).cumcount()
spread = PARALLEL_SPACING * (pair_rank - (pair_size - 1) / 2)
trim = NODE_CLEARANCE / length

edges["seg_x"] = edges[SOURCE_X] + dx * trim + perp_x * spread
edges["seg_y"] = edges[SOURCE_Y] + dy * trim + perp_y * spread
edges["seg_xend"] = edges[TARGET_X] - dx * trim + perp_x * spread
edges["seg_yend"] = edges[TARGET_Y] - dy * trim + perp_y * spread
# Each label sits on the outer side of its own edge, so parallel routes never label across each other
label_side = np.where(spread < 0, -1, 1)
edges["mid_x"] = (edges[SOURCE_X] + edges[TARGET_X]) / 2 + perp_x * (label_side * LABEL_OFFSET + spread)
edges["mid_y"] = (edges[SOURCE_Y] + edges[TARGET_Y]) / 2 + perp_y * (label_side * LABEL_OFFSET + spread)
edges["edge_label"] = edges[ROUTE] + " | " + edges[DEPARTURE] + " → " + edges[ARRIVAL]

edge_tooltips = (
    layer_tooltips()
    .title(f"@{ROUTE}")
    .line(f"@{SOURCE_NAME} → @{TARGET_NAME}")
    .line(f"Departs: @{DEPARTURE}")
    .line(f"Arrives: @{ARRIVAL}")
    .line(f"Type: @{{{ROUTE_TYPE}}}")
)
station_tooltips = layer_tooltips().title("@node_name").line("Station ID: @node_id")

plot = (
    ggplot()
    + geom_segment(
        aes(x="seg_x", y="seg_y", xend="seg_xend", yend="seg_yend", color=ROUTE_TYPE),
        data=edges,
        size=1.0,
        alpha=0.85,
        arrow=arrow(angle=25, length=7, type="closed"),
        tooltips=edge_tooltips,
    )
    + geom_text(aes(x="mid_x", y="mid_y", label="edge_label", color=ROUTE_TYPE), data=edges, size=3.5)
    + geom_point(
        aes(x="node_x", y="node_y"),
        data=nodes,
        size=6,
        color="white",
        shape=21,
        fill=IMPRINT_PALETTE[0],
        stroke=1.2,
        tooltips=station_tooltips,
    )
    + geom_text(
        aes(x="node_x", y="node_y", label="node_name"), data=nodes, size=5, color=INK, fontface="bold", nudge_y=-0.055
    )
    + scale_color_manual(values=route_colors, breaks=route_types, name=ROUTE_TYPE)
    + labs(title="network-transport-static · python · letsplot · anyplot.ai", x="", y="")
    + theme_void()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=14, face="bold", hjust=0.5, color=INK),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=9, color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
    )
    + scale_x_continuous(limits=[0, 1])
    + scale_y_continuous(limits=[0, 1])
    + ggsize(800, 450)
)

# Save as PNG (scale 4x for 3200x1800) and as interactive HTML
ggsave(plot, f"plot-{THEME}.png", scale=4, path=".")
ggsave(plot, f"plot-{THEME}.html", path=".")
