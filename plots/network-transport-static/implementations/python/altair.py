""" anyplot.ai
network-transport-static: Static Transport Network Diagram
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-22
"""

import os
import sys


# Handle naming conflict: remove script dir from path before importing
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != script_dir]

import altair as alt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per route type in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
SHRINK_PX = 3  # gap between an edge end and the node outline
EDGE_SPACING_PX = 15  # distance between parallel routes of one station pair

# Columns: set these to your table's column names
SOURCE_ID = "Source station"  # role: routes
TARGET_ID = "Target station"  # role: extra
ROUTE_ID = "Route"  # role: extra
DEPARTURE = "Departure"  # role: extra
ARRIVAL = "Arrival"  # role: extra
ROUTE_TYPE = "Route type"  # role: extra
STATION_ID = "Station"  # role: stations
STATION_LABEL = "Station name"  # role: extra
X = "x position"  # role: extra
Y = "y position"  # role: extra

# Data: regional rail network, one row per directed route; replace with your own tables,
# for example df = pd.read_csv("routes.csv") and nodes = pd.read_csv("stations.csv")
nodes = pd.DataFrame(
    {
        STATION_ID: list("ABCDEFGHIJKL"),
        STATION_LABEL: [
            "Central Station",
            "North Terminal",
            "East Junction",
            "West Gate",
            "South Park",
            "Airport",
            "University",
            "Harbor",
            "Tech Campus",
            "Old Town",
            "Business District",
            "Riverside",
        ],
        X: [400, 400, 700, 100, 400, 750, 700, 100, 550, 250, 550, 250],
        Y: [450, 100, 300, 300, 750, 100, 600, 600, 200, 200, 550, 550],
    }
)
df = pd.DataFrame(
    [
        # Express lines
        ("A", "B", "RE1", "06:00", "06:25", "Express"),
        ("B", "A", "RE1", "06:35", "07:00", "Express"),
        ("A", "F", "RE2", "07:00", "07:45", "Express"),
        ("F", "A", "RE2", "08:00", "08:45", "Express"),
        ("A", "E", "RE3", "06:15", "06:40", "Express"),
        ("E", "A", "RE3", "07:00", "07:25", "Express"),
        # Regional lines
        ("B", "F", "RB1", "07:15", "07:35", "Regional"),
        ("F", "B", "RB1", "08:00", "08:20", "Regional"),
        ("B", "I", "RB2", "06:30", "06:45", "Regional"),
        ("I", "C", "RB2", "06:50", "07:05", "Regional"),
        ("B", "J", "RB3", "07:00", "07:15", "Regional"),
        ("J", "D", "RB3", "07:20", "07:35", "Regional"),
        # Local services
        ("A", "K", "S1", "06:10", "06:22", "Local"),
        ("K", "G", "S1", "06:25", "06:40", "Local"),
        ("G", "C", "S1", "06:45", "07:00", "Local"),
        ("A", "L", "S2", "06:20", "06:32", "Local"),
        ("L", "H", "S2", "06:35", "06:50", "Local"),
        ("H", "D", "S2", "06:55", "07:10", "Local"),
        ("D", "A", "S3", "07:30", "07:50", "Local"),
        ("C", "A", "S4", "07:15", "07:35", "Local"),
        ("E", "K", "S5", "08:00", "08:15", "Local"),
        ("E", "L", "S6", "08:10", "08:25", "Local"),
        ("K", "A", "S1", "07:30", "07:42", "Local"),
        ("L", "A", "S2", "07:40", "07:52", "Local"),
    ],
    columns=[SOURCE_ID, TARGET_ID, ROUTE_ID, DEPARTURE, ARRIVAL, ROUTE_TYPE],
)

# Plot: reads only df, nodes and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
VIEW_W, VIEW_H = 540, 520

# Equal scale on both axes: the view shows the station box plus a margin, centred
pad = 60
x_mid, y_mid = nodes[X].agg(["min", "max"]).mean(), nodes[Y].agg(["min", "max"]).mean()
units_per_px = max(
    (nodes[X].max() - nodes[X].min() + 2 * pad) / VIEW_W, (nodes[Y].max() - nodes[Y].min() + 2 * pad) / VIEW_H
)
x_scale = alt.Scale(domain=[x_mid - VIEW_W * units_per_px / 2, x_mid + VIEW_W * units_per_px / 2], nice=False)
y_scale = alt.Scale(
    domain=[y_mid - VIEW_H * units_per_px / 2, y_mid + VIEW_H * units_per_px / 2], reverse=True, nice=False
)

NODE_SIZE = 560  # mark area in px^2
node_radius = np.sqrt(NODE_SIZE / np.pi) * units_per_px  # in data units

# Parallel routes between one station pair become offset edges
pair = df[[SOURCE_ID, TARGET_ID]].apply(lambda r: "|".join(sorted(r)), axis=1)
pair_index = df.groupby(pair).cumcount()
pair_count = df.groupby(pair)[SOURCE_ID].transform("size")
offset = (pair_index - (pair_count - 1) / 2) * EDGE_SPACING_PX * units_per_px

pos = nodes.set_index(STATION_ID)[[X, Y]]
src, tgt = pos.loc[df[SOURCE_ID]].to_numpy(), pos.loc[df[TARGET_ID]].to_numpy()
delta = tgt - src
length = np.hypot(delta[:, 0], delta[:, 1])
ux, uy = delta[:, 0] / length, delta[:, 1] / length
# Offset edges are perpendicular to the straight line; routes of one pair run opposite ways, so the
# sign flips with direction and the two lines land on opposite sides
sign = np.where(df[SOURCE_ID] < df[TARGET_ID], 1, -1)
px, py = -uy * offset.to_numpy() * sign, ux * offset.to_numpy() * sign
trim = node_radius + SHRINK_PX * units_per_px

edges = pd.DataFrame(
    {
        "x1": src[:, 0] + px + ux * trim,
        "y1": src[:, 1] + py + uy * trim,
        "x2": tgt[:, 0] + px - ux * trim,
        "y2": tgt[:, 1] + py - uy * trim,
        ROUTE_TYPE: df[ROUTE_TYPE],
        ROUTE_ID: df[ROUTE_ID],
        DEPARTURE: df[DEPARTURE],
        ARRIVAL: df[ARRIVAL],
    }
)
heading = np.degrees(np.arctan2(uy, ux))  # clockwise from +x on screen, because the y scale is reversed
edges["head_x"] = edges["x2"] - ux * 5 * units_per_px
edges["head_y"] = edges["y2"] - uy * 5 * units_per_px
edges["head_angle"] = heading + 90  # the triangle shape points up at angle 0
edges["mid_x"] = (edges["x1"] + edges["x2"]) / 2 - ux * 3 * units_per_px
edges["mid_y"] = (edges["y1"] + edges["y2"]) / 2 - uy * 3 * units_per_px
edges["text_angle"] = np.where(np.abs(heading) > 90, heading + 180, heading)  # keep text upright
edges["label"] = edges[ROUTE_ID] + " | " + edges[DEPARTURE] + "→" + edges[ARRIVAL]

route_types = list(df[ROUTE_TYPE].unique())
type_color = alt.Color(
    ROUTE_TYPE.translate(ESCAPE),
    type="nominal",
    title=ROUTE_TYPE,
    sort=None,
    scale=alt.Scale(domain=route_types, range=IMPRINT_PALETTE),
)


def xy(x, y):
    return {"x": alt.X(x, type="quantitative", scale=x_scale), "y": alt.Y(y, type="quantitative", scale=y_scale)}


lines = (
    alt.Chart(edges)
    .mark_rule(strokeWidth=1.6, opacity=0.9)
    .encode(
        **xy("x1", "y1"),
        x2="x2:Q",
        y2="y2:Q",
        color=type_color,
        tooltip=[
            alt.Tooltip(ROUTE_ID.translate(ESCAPE), title=ROUTE_ID),
            alt.Tooltip(DEPARTURE.translate(ESCAPE), title=DEPARTURE),
            alt.Tooltip(ARRIVAL.translate(ESCAPE), title=ARRIVAL),
            alt.Tooltip(ROUTE_TYPE.translate(ESCAPE), title=ROUTE_TYPE),
        ],
    )
)

heads = (
    alt.Chart(edges)
    .mark_point(shape="triangle", size=70, filled=True, opacity=1)
    .encode(
        **xy("head_x", "head_y"),
        angle=alt.Angle("head_angle:Q", scale=None),
        color=alt.Color(
            ROUTE_TYPE.translate(ESCAPE),
            type="nominal",
            sort=None,
            scale=alt.Scale(domain=route_types, range=IMPRINT_PALETTE),
        ),
    )
)

node_marks = (
    alt.Chart(nodes)
    .mark_circle(size=NODE_SIZE, stroke=INK_SOFT, strokeWidth=1.2, opacity=1)
    .encode(**xy(X, Y), color=alt.value(ELEVATED_BG))
)
node_ids = (
    alt.Chart(nodes)
    .mark_text(fontSize=11, fontWeight="bold")
    .encode(**xy(X, Y), text=alt.Text(STATION_ID.translate(ESCAPE), type="nominal"), color=alt.value(INK))
)
# Station names go on the side of the node that its routes leave free
incident = {sid: [] for sid in nodes[STATION_ID]}
for sid_a, sid_b, ex, ey in zip(df[SOURCE_ID], df[TARGET_ID], ux, uy, strict=True):
    incident[sid_a].append((ex, ey))
    incident[sid_b].append((-ex, -ey))
# side: (unit vector on screen, text align, tie-break penalty); corners keep names clear of diagonal routes
H = 0.7071
SIDES = {
    "left": ((-1, 0), "right", 0),
    "right": ((1, 0), "left", 0),
    "above": ((0, -1), "center", 0.05),
    "below": ((0, 1), "center", 0.05),
    "upper_left": ((-H, -H), "right", 0.1),
    "upper_right": ((H, -H), "left", 0.1),
    "lower_left": ((-H, H), "right", 0.1),
    "lower_right": ((H, H), "left", 0.1),
}
side_of = {}
for sid in nodes[STATION_ID]:
    clash = {k: max(v[0] * c[0][0] + v[1] * c[0][1] for v in incident[sid]) + c[2] for k, c in SIDES.items()}
    side_of[sid] = min(clash, key=clash.get)
name_layers = []
for side, ((sx, sy), align, _) in SIDES.items():
    picked = nodes[nodes[STATION_ID].map(side_of) == side]
    if picked.empty:
        continue
    gap = 24 if sx == 0 else 22 if sy == 0 else 17
    names = picked.assign(name_x=picked[X] + sx * gap * units_per_px, name_y=picked[Y] + sy * gap * units_per_px)
    enc = dict(**xy("name_x", "name_y"), text=alt.Text(STATION_LABEL.translate(ESCAPE), type="nominal"))
    name_layers.append(
        alt.Chart(names)
        .mark_text(fontSize=9.5, fontWeight="bold", stroke=PAGE_BG, strokeWidth=3, strokeJoin="round", align=align)
        .encode(**enc, color=alt.value(PAGE_BG))
    )
    name_layers.append(
        alt.Chart(names).mark_text(fontSize=9.5, fontWeight="bold", align=align).encode(**enc, color=alt.value(INK))
    )

# Each route label sits on its own edge, rotated along it, over a halo in the page color
label_halo = (
    alt.Chart(edges)
    .mark_text(fontSize=7.5, fontWeight="bold", stroke=PAGE_BG, strokeWidth=3, strokeJoin="round")
    .encode(
        **xy("mid_x", "mid_y"), text="label:N", angle=alt.Angle("text_angle:Q", scale=None), color=alt.value(PAGE_BG)
    )
)
label_text = (
    alt.Chart(edges)
    .mark_text(fontSize=7.5, fontWeight="bold")
    .encode(**xy("mid_x", "mid_y"), text="label:N", angle=alt.Angle("text_angle:Q", scale=None), color=alt.value(INK))
)

chart = (
    alt.layer(lines, heads, node_marks, node_ids, *name_layers, label_halo, label_text)
    .properties(
        width=VIEW_W,
        height=VIEW_H,
        background=PAGE_BG,
        padding={"left": 10, "right": 10, "top": 10, "bottom": 10},
        title=alt.Title("network-transport-static · python · altair · anyplot.ai", fontSize=16, color=INK),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_axis(grid=False, labels=False, ticks=False, domain=False, title=None)
    .configure_legend(
        orient="top-left",
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=11,
        symbolType="stroke",
        symbolStrokeWidth=3,
        padding=6,
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) the PNG to the canonical square canvas
TW, TH = 2400, 2400
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair vl-convert produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
