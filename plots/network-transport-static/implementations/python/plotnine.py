"""anyplot.ai
network-transport-static: Static Transport Network Diagram
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-18
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    arrow,
    element_rect,
    element_text,
    geom_label,
    geom_point,
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per route type in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
TYPE_NAMES = {"VE": "VE (Valley express)", "R": "R (Regional)", "CB": "CB (Cog railway)", "SK": "SK (Ski shuttle)"}
LANE_GAP = 0.6  # distance between parallel edges of one station pair, in map units
NODE_RADIUS = 0.3  # edges stop this far from a station centre so arrowheads stay visible

# Columns: set these to your tables' column names
STATIONS = ["id", "label", "x", "y"]  # role: stations
ROUTES = ["source_id", "target_id", "route_id", "departure_time", "arrival_time"]  # role: routes
NODE_ID, NODE_LABEL, X, Y = STATIONS
SOURCE, TARGET, ROUTE, DEPARTURE, ARRIVAL = ROUTES

# Data: replace this block with your own tables, for example df = pd.read_csv("routes.csv")
# An alpine valley line: schematic station coordinates, one row per directed service
nodes = pd.DataFrame(
    {
        NODE_ID: ["TAL", "SEE", "SON", "ALM", "LAR", "GLE", "BER", "KRE", "HOC", "EIS", "WIE"],
        NODE_LABEL: [
            "Talbach",
            "Seewald",
            "Sonnalp",
            "Almdorf",
            "Larchau",
            "Gletscherhof",
            "Bergstein",
            "Kreuzjoch",
            "Hochmoos",
            "Eisbach",
            "Wiesental",
        ],
        X: [7.5, 2.8, 1.6, 4.6, 4.5, 8.0, 10.6, 12.0, 14.2, 9.6, 14.0],
        Y: [4.2, 3.6, 6.9, 6.0, 1.6, 7.9, 6.4, 4.0, 7.2, 1.4, 2.0],
    }
)

services = [
    ("SEE", "TAL", "VE1", "06:40", "07:05"),
    ("TAL", "KRE", "VE1", "07:10", "07:38"),
    ("KRE", "TAL", "VE2", "08:00", "08:28"),
    ("TAL", "SEE", "VE2", "08:33", "08:58"),
    ("TAL", "BER", "VE3", "10:00", "10:24"),
    ("TAL", "ALM", "R1", "07:15", "07:35"),
    ("ALM", "SON", "R1", "07:40", "07:58"),
    ("ALM", "TAL", "R2", "08:10", "08:30"),
    ("TAL", "LAR", "R3", "07:45", "08:05"),
    ("LAR", "SEE", "R3", "08:10", "08:30"),
    ("TAL", "EIS", "R4", "09:00", "09:22"),
    ("EIS", "WIE", "R4", "09:27", "09:52"),
    ("WIE", "KRE", "R5", "10:05", "10:25"),
    ("KRE", "BER", "R5", "10:30", "10:50"),
    ("HOC", "BER", "R6", "11:00", "11:25"),
    ("BER", "GLE", "CB1", "08:20", "08:42"),
    ("GLE", "BER", "CB1", "09:10", "09:31"),
    ("KRE", "HOC", "CB2", "09:15", "09:40"),
    ("HOC", "KRE", "CB2", "10:05", "10:30"),
    ("TAL", "GLE", "SK1", "08:00", "08:35"),
    ("GLE", "TAL", "SK1", "16:00", "16:35"),
    ("TAL", "BER", "SK2", "10:10", "10:38"),
    ("BER", "TAL", "SK2", "11:00", "11:24"),
    ("SON", "SEE", "SK3", "12:00", "12:26"),
]
df = pd.DataFrame(services, columns=[SOURCE, TARGET, ROUTE, DEPARTURE, ARRIVAL])

# Plot: reads only df, nodes and the constants above
coords = nodes.set_index(NODE_ID)[[X, Y]]
edges = df.copy()
edges["x0"] = edges[SOURCE].map(coords[X])
edges["y0"] = edges[SOURCE].map(coords[Y])
edges["x1"] = edges[TARGET].map(coords[X])
edges["y1"] = edges[TARGET].map(coords[Y])
edges["route_type"] = edges[ROUTE].str.extract(r"^([A-Za-z]+)")[0]
types = edges["route_type"].unique().tolist()

# Parallel services of one station pair get their own lane, centred on the straight line
pair_key = edges[[SOURCE, TARGET]].apply(lambda r: "|".join(sorted(r)), axis=1)
lane = edges.groupby(pair_key).cumcount() - (edges.groupby(pair_key)[SOURCE].transform("size") - 1) / 2
canon_forward = (edges[SOURCE] < edges[TARGET]).map({True: 1.0, False: -1.0})
dx = edges["x1"] - edges["x0"]
dy = edges["y1"] - edges["y0"]
length = np.hypot(dx, dy)
ux, uy = dx / length, dy / length
shift = lane * LANE_GAP * canon_forward
px, py = -uy * shift, ux * shift

edges["xs"] = edges["x0"] + px + ux * NODE_RADIUS
edges["ys"] = edges["y0"] + py + uy * NODE_RADIUS
edges["xe"] = edges["x1"] + px - ux * NODE_RADIUS
edges["ye"] = edges["y1"] + py - uy * NODE_RADIUS

# Label sits on its own edge, at staggered positions so neighbours do not stack
t = 0.5 + 0.14 * lane * canon_forward
edges["lx"] = edges["xs"] + (edges["xe"] - edges["xs"]) * t
edges["ly"] = edges["ys"] + (edges["ye"] - edges["ys"]) * t
edges["tag"] = edges[ROUTE] + "  " + edges[DEPARTURE] + "→" + edges[ARRIVAL]

x_pad = (nodes[X].max() - nodes[X].min()) * 0.06
y_pad = (nodes[Y].max() - nodes[Y].min()) * 0.14

plot = (
    ggplot()
    + geom_segment(
        data=edges,
        mapping=aes(x="xs", y="ys", xend="xe", yend="ye", color="route_type"),
        size=0.8,
        arrow=arrow(length=0.07, type="closed", angle=25),
    )
    + geom_point(data=nodes, mapping=aes(x=X, y=Y), size=6, fill=ELEVATED_BG, color=INK, stroke=1)
    + geom_label(
        data=edges,
        mapping=aes(x="lx", y="ly", label="tag", color="route_type"),
        size=5.5,
        fill=PAGE_BG,
        label_size=0,
        label_padding=0.08,
        fontweight="bold",
        show_legend=False,
    )
    + geom_label(
        data=nodes,
        mapping=aes(x=X, y=Y, label=NODE_LABEL),
        size=8,
        fontweight="bold",
        color=INK,
        fill=PAGE_BG,
        label_size=0,
        label_padding=0.1,
        nudge_y=0.62,
    )
    + scale_color_manual(
        values=IMPRINT_PALETTE, limits=types, labels=[TYPE_NAMES.get(name, name) for name in types], name="Route type"
    )
    + scale_x_continuous(limits=(nodes[X].min() - x_pad, nodes[X].max() + x_pad))
    + scale_y_continuous(limits=(nodes[Y].min() - y_pad, nodes[Y].max() + y_pad))
    + labs(title="network-transport-static · python · plotnine · anyplot.ai")
    + theme_void()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_title=element_text(size=9, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
