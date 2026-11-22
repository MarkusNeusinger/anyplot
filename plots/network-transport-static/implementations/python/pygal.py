"""anyplot.ai
network-transport-static: Static Transport Network Diagram
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-11-22
"""

import os
import xml.etree.ElementTree as ET

import cairosvg
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"

# Imprint palette
IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Constants
WIDTH = 3200
HEIGHT = 1800
MARGIN_X = 100
MARGIN_TOP = 170
MARGIN_BOTTOM = 100
ROUTE_TYPES = {"RE": "Regional Express", "EX": "Express", "LO": "Local"}

# Column names
SOURCE = "source"  # role: routes
TARGET = "target"  # role: routes
ROUTE_ID = "route_id"  # role: routes
DEPARTURE = "departure_time"  # role: routes
ARRIVAL = "arrival_time"  # role: routes
SRC_X = "source_x"  # role: routes
SRC_Y = "source_y"  # role: routes
TGT_X = "target_x"  # role: routes
TGT_Y = "target_y"  # role: routes

# Data: regional rail network, one row per train service
services = [
    ("Central Station", "North Park", "RE 1", "06:00", "06:25", 0.08, 0.5, 0.25, 0.2),
    ("Central Station", "South Gate", "RE 2", "06:15", "06:45", 0.08, 0.5, 0.25, 0.8),
    ("North Park", "East Harbor", "RE 1", "06:30", "07:00", 0.25, 0.2, 0.5, 0.3),
    ("North Park", "Airport", "EX 10", "07:00", "07:40", 0.25, 0.2, 0.75, 0.18),
    ("East Harbor", "Airport", "RE 3", "07:10", "07:35", 0.5, 0.3, 0.75, 0.18),
    ("East Harbor", "University", "RE 4", "07:20", "07:50", 0.5, 0.3, 0.75, 0.5),
    ("South Gate", "West Valley", "RE 5", "06:50", "07:25", 0.25, 0.8, 0.5, 0.65),
    ("South Gate", "Riverside", "LO 20", "07:00", "07:20", 0.25, 0.8, 0.5, 0.88),
    ("West Valley", "University", "RE 5", "07:30", "07:55", 0.5, 0.65, 0.75, 0.5),
    ("West Valley", "Industrial Zone", "RE 6", "07:35", "08:00", 0.5, 0.65, 0.75, 0.78),
    ("West Valley", "Riverside", "LO 21", "07:40", "07:55", 0.5, 0.65, 0.5, 0.88),
    ("Airport", "University", "EX 10", "07:45", "08:05", 0.75, 0.18, 0.75, 0.5),
    ("University", "Tech Campus", "EX 11", "08:10", "08:30", 0.75, 0.5, 0.92, 0.5),
    ("University", "Industrial Zone", "RE 7", "08:00", "08:20", 0.75, 0.5, 0.75, 0.78),
    ("Industrial Zone", "Riverside", "RE 8", "08:25", "08:50", 0.75, 0.78, 0.5, 0.88),
]
df = pd.DataFrame(services, columns=[SOURCE, TARGET, ROUTE_ID, DEPARTURE, ARRIVAL, SRC_X, SRC_Y, TGT_X, TGT_Y])

# Plot
plot_width = WIDTH - 2 * MARGIN_X
plot_height = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
NODE_R = 36
OFFSET_STEP = 26


def to_svg(x_norm, y_norm):
    return MARGIN_X + x_norm * plot_width, MARGIN_TOP + y_norm * plot_height


# Route type colors: Imprint positions 1-3, one per type found in the data
# Stations derived from the routes: unique names with their position, in first-seen order
stations = dict(
    zip(
        pd.concat([df[SOURCE], df[TARGET]]),
        zip(pd.concat([df[SRC_X], df[TGT_X]]), pd.concat([df[SRC_Y], df[TGT_Y]]), strict=True),
        strict=True,
    )
)

route_types = list(dict.fromkeys(df[ROUTE_ID].str.split().str[0]))
route_colors = {t: IMPRINT[i % len(IMPRINT)] for i, t in enumerate(route_types)}

svg_ns = "http://www.w3.org/2000/svg"
ET.register_namespace("", svg_ns)
svg_root = ET.Element("svg", xmlns=svg_ns, width=str(WIDTH), height=str(HEIGHT), viewBox=f"0 0 {WIDTH} {HEIGHT}")
svg_root.set("style", f"background-color: {PAGE_BG};")

defs = ET.SubElement(svg_root, "defs")
for prefix, color in route_colors.items():
    marker = ET.SubElement(
        defs,
        "marker",
        id=f"arrow-{prefix}",
        markerWidth="10",
        markerHeight="10",
        refX="8",
        refY="4",
        orient="auto",
        markerUnits="strokeWidth",
    )
    ET.SubElement(marker, "path", d="M0,0 L0,8 L10,4 z", fill=color)

bg = ET.SubElement(svg_root, "rect", x="0", y="0", width=str(WIDTH), height=str(HEIGHT), fill=PAGE_BG)

title_elem = ET.SubElement(
    svg_root,
    "text",
    {
        "x": str(WIDTH / 2),
        "y": "75",
        "text-anchor": "middle",
        "fill": INK,
        "font-size": "58",
        "font-family": "sans-serif",
        "font-weight": "bold",
    },
)
title_elem.text = "network-transport-static · python · pygal · anyplot.ai"
subtitle_elem = ET.SubElement(
    svg_root,
    "text",
    {
        "x": str(WIDTH / 2),
        "y": "125",
        "text-anchor": "middle",
        "fill": INK_SOFT,
        "font-size": "34",
        "font-family": "sans-serif",
    },
)
subtitle_elem.text = "Regional Rail Network - Morning Schedule"

edges_g = ET.SubElement(svg_root, "g", {"class": "routes"})

# Parallel services between the same station pair are offset perpendicular to the edge
pair_key = df.apply(lambda r: tuple(sorted([r[SOURCE], r[TARGET]])), axis=1)
pair_total = pair_key.map(pair_key.value_counts())
pair_index = pair_key.groupby(pair_key).cumcount()

for i, route in df.iterrows():
    x1, y1 = to_svg(route[SRC_X], route[SRC_Y])
    x2, y2 = to_svg(route[TGT_X], route[TGT_Y])
    prefix = route[ROUTE_ID].split()[0]
    color = route_colors[prefix]

    dx, dy = x2 - x1, y2 - y1
    length = (dx**2 + dy**2) ** 0.5
    ux, uy = dx / length, dy / length
    shift = (pair_index[i] - (pair_total[i] - 1) / 2) * OFFSET_STEP
    ox, oy = -uy * shift, ux * shift
    x1, y1 = x1 + ox + ux * NODE_R, y1 + oy + uy * NODE_R
    x2, y2 = x2 + ox - ux * NODE_R, y2 + oy - uy * NODE_R

    line = ET.SubElement(
        edges_g,
        "line",
        {
            "x1": f"{x1:.1f}",
            "y1": f"{y1:.1f}",
            "x2": f"{x2:.1f}",
            "y2": f"{y2:.1f}",
            "stroke": color,
            "stroke-width": "4",
            "stroke-opacity": "0.85",
            "marker-end": f"url(#arrow-{prefix})",
        },
    )
    label_text = f"{route[ROUTE_ID]} | {route[DEPARTURE]} → {route[ARRIVAL]}"
    ET.SubElement(line, "title").text = f"{route[ROUTE_ID]}: {route[DEPARTURE]} → {route[ARRIVAL]}"

    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    box_w = 13.5 * len(label_text) + 24
    ET.SubElement(
        edges_g,
        "rect",
        {
            "x": f"{mid_x - box_w / 2:.1f}",
            "y": f"{mid_y - 21:.1f}",
            "width": f"{box_w:.1f}",
            "height": "42",
            "fill": ELEVATED_BG,
            "fill-opacity": "0.95",
            "rx": "7",
            "stroke": color,
            "stroke-width": "1.5",
            "stroke-opacity": "0.6",
        },
    )
    label_elem = ET.SubElement(
        edges_g,
        "text",
        {
            "x": f"{mid_x:.1f}",
            "y": f"{mid_y + 8:.1f}",
            "text-anchor": "middle",
            "fill": INK,
            "font-size": "24",
            "font-family": "sans-serif",
            "font-weight": "600",
        },
    )
    label_elem.text = label_text

nodes_g = ET.SubElement(svg_root, "g", {"class": "stations"})
for n, (name, (sx, sy)) in enumerate(stations.items()):
    x, y = to_svg(sx, sy)
    circle = ET.SubElement(
        nodes_g,
        "circle",
        {"cx": f"{x:.1f}", "cy": f"{y:.1f}", "r": str(NODE_R), "fill": IMPRINT[0], "stroke": INK, "stroke-width": "4"},
    )
    ET.SubElement(circle, "title").text = name
    id_elem = ET.SubElement(
        nodes_g,
        "text",
        {
            "x": f"{x:.1f}",
            "y": f"{y + 11:.1f}",
            "text-anchor": "middle",
            "fill": PAGE_BG,
            "font-size": "32",
            "font-family": "sans-serif",
            "font-weight": "bold",
        },
    )
    id_elem.text = chr(ord("A") + n)

    box_w = 15.5 * len(name) + 30
    ET.SubElement(
        nodes_g,
        "rect",
        {
            "x": f"{x - box_w / 2:.1f}",
            "y": f"{y + NODE_R + 8:.1f}",
            "width": f"{box_w:.1f}",
            "height": "44",
            "fill": ELEVATED_BG,
            "fill-opacity": "0.95",
            "rx": "7",
            "stroke": INK_MUTED,
            "stroke-width": "1.5",
            "stroke-opacity": "0.5",
        },
    )
    name_elem = ET.SubElement(
        nodes_g,
        "text",
        {
            "x": f"{x:.1f}",
            "y": f"{y + NODE_R + 40:.1f}",
            "text-anchor": "middle",
            "fill": INK,
            "font-size": "28",
            "font-family": "sans-serif",
            "font-weight": "600",
        },
    )
    name_elem.text = name

# Legend
legend_g = ET.SubElement(svg_root, "g", {"class": "legend"})
legend_w, legend_h = 520, 60 + 48 * len(route_types)
legend_x = WIDTH - MARGIN_X - legend_w
legend_y = HEIGHT - MARGIN_BOTTOM - legend_h + 30
ET.SubElement(
    legend_g,
    "rect",
    {
        "x": str(legend_x),
        "y": str(legend_y),
        "width": str(legend_w),
        "height": str(legend_h),
        "fill": ELEVATED_BG,
        "fill-opacity": "0.95",
        "stroke": INK_MUTED,
        "stroke-width": "2",
        "stroke-opacity": "0.5",
        "rx": "10",
    },
)
ET.SubElement(
    legend_g,
    "text",
    {
        "x": str(legend_x + 30),
        "y": str(legend_y + 45),
        "fill": INK,
        "font-size": "32",
        "font-family": "sans-serif",
        "font-weight": "bold",
    },
).text = "Route types"
for i, prefix in enumerate(route_types):
    ly = legend_y + 90 + i * 48
    color = route_colors[prefix]
    ET.SubElement(
        legend_g,
        "line",
        {
            "x1": str(legend_x + 30),
            "y1": str(ly),
            "x2": str(legend_x + 90),
            "y2": str(ly),
            "stroke": color,
            "stroke-width": "5",
        },
    )
    ET.SubElement(
        legend_g,
        "polygon",
        {"points": f"{legend_x + 90},{ly - 10} {legend_x + 90},{ly + 10} {legend_x + 112},{ly}", "fill": color},
    )
    ET.SubElement(
        legend_g,
        "text",
        {"x": str(legend_x + 130), "y": str(ly + 10), "fill": INK_SOFT, "font-size": "28", "font-family": "sans-serif"},
    ).text = f"{prefix} - {ROUTE_TYPES.get(prefix, prefix)}"

svg_output = ET.tostring(svg_root, encoding="unicode")

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>network-transport-static - pygal - anyplot.ai</title>
    <style>
        body {{ margin: 0; padding: 20px; background: {PAGE_BG}; font-family: sans-serif; }}
        .container {{ max-width: 100%; overflow: auto; }}
        svg {{ display: block; margin: 0 auto; max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <div class="container">
        {svg_output}
    </div>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

cairosvg.svg2png(
    bytestring=svg_output.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=WIDTH, output_height=HEIGHT
)
