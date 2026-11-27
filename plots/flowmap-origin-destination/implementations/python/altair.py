"""anyplot.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: altair 6.3.0 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-27
"""

import os

import altair as alt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MAP_FILL = "#D8D6CE" if THEME == "light" else "#2D2D2A"

# Imprint palette: position 1 colors the city markers
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for marks (colored lines on the page), low -> high flow
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.687, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#6F7E20"), (0.21, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants
ARC_POINTS = 50  # vertices per Bezier arc
ARC_BEND = 0.3  # control-point offset as a share of the origin-destination vector
MIN_WIDTH, MAX_WIDTH = 0.5, 6.0  # arc stroke widths for the smallest and largest flow
LABEL_OFFSET = {"London": (-15, -14), "Paris": (-12, -14), "Amsterdam": (14, -14), "Brussels": (16, 12)}
DEFAULT_LABEL_OFFSET = (0, -14)  # label above its marker unless the dense cluster needs a nudge

# Columns: set these to your table's column names
ORIGIN = "Origin"  # role: origin_name
DEST = "Destination"  # role: dest_name
ORIGIN_LAT = "Origin latitude"  # role: origin_lat
ORIGIN_LON = "Origin longitude"  # role: origin_lon
DEST_LAT = "Destination latitude"  # role: dest_lat
DEST_LON = "Destination longitude"  # role: dest_lon
FLOW = "Flow volume"  # role: flow

# Data: replace this block with your own table, for example df = pd.read_csv("flows.csv")
# Migration flows between major European cities
np.random.seed(42)
cities = {
    "London": (51.5074, -0.1278),
    "Paris": (48.8566, 2.3522),
    "Berlin": (52.5200, 13.4050),
    "Madrid": (40.4168, -3.7038),
    "Rome": (41.9028, 12.4964),
    "Amsterdam": (52.3676, 4.9041),
    "Vienna": (48.2082, 16.3738),
    "Brussels": (50.8503, 4.3517),
    "Lisbon": (38.7223, -9.1393),
    "Dublin": (53.3498, -6.2603),
}
hubs = ["London", "Paris", "Berlin"]
pairs = [(hub, dest, np.random.randint(5000, 50000)) for hub in hubs for dest in cities if dest != hub]
pairs += [(origin, hub, np.random.randint(2000, 20000)) for origin in ["Madrid", "Rome", "Amsterdam"] for hub in hubs]
df = pd.DataFrame(
    {
        ORIGIN: [p[0] for p in pairs],
        DEST: [p[1] for p in pairs],
        ORIGIN_LAT: [cities[p[0]][0] for p in pairs],
        ORIGIN_LON: [cities[p[0]][1] for p in pairs],
        DEST_LAT: [cities[p[1]][0] for p in pairs],
        DEST_LON: [cities[p[1]][1] for p in pairs],
        FLOW: [p[2] for p in pairs],
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
flow_min, flow_max = df[FLOW].min(), df[FLOW].max()

# Bezier arc per flow; a pair's two directions bend opposite ways so the corridors separate
t = np.linspace(0, 1, ARC_POINTS)
arc_rows = []
for _, row in df.iterrows():
    x0, y0, x1, y1 = row[ORIGIN_LON], row[ORIGIN_LAT], row[DEST_LON], row[DEST_LAT]
    origin, dest, flow = row[ORIGIN], row[DEST], row[FLOW]
    sign = 1 if origin < dest else -1
    ctrl_x = (x0 + x1) / 2 - (y1 - y0) * ARC_BEND * sign
    ctrl_y = (y0 + y1) / 2 + (x1 - x0) * ARC_BEND * sign
    arc = pd.DataFrame(
        {
            "flow_id": f"{origin}-{dest}",
            "order": np.arange(ARC_POINTS),
            "lon": (1 - t) ** 2 * x0 + 2 * (1 - t) * t * ctrl_x + t**2 * x1,
            "lat": (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ctrl_y + t**2 * y1,
            ORIGIN: origin,
            DEST: dest,
            FLOW: flow,
        }
    )
    arc_rows.append(arc)
arcs_df = pd.concat(arc_rows, ignore_index=True)
span = max(flow_max - flow_min, 1)
arcs_df["stroke_width"] = MIN_WIDTH + (MAX_WIDTH - MIN_WIDTH) * (arcs_df[FLOW] - flow_min) / span

# One row per city, with its label offset
cities_df = (
    pd.concat(
        [
            df[[ORIGIN, ORIGIN_LAT, ORIGIN_LON]].set_axis(["city", "lat", "lon"], axis=1),
            df[[DEST, DEST_LAT, DEST_LON]].set_axis(["city", "lat", "lon"], axis=1),
        ]
    )
    .drop_duplicates("city")
    .reset_index(drop=True)
)
offsets = cities_df["city"].map(lambda c: LABEL_OFFSET.get(c, DEFAULT_LABEL_OFFSET))
cities_df["dx"] = [o[0] for o in offsets]
cities_df["dy"] = [o[1] for o in offsets]

# Geographic projection centered on Europe
world = alt.topo_feature("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json", "countries")
proj = {"type": "mercator", "scale": 700, "center": [4.5, 47.5]}

base = alt.Chart(world).mark_geoshape(fill=MAP_FILL, stroke=PAGE_BG, strokeWidth=0.5).project(**proj)

arcs = (
    alt.Chart(arcs_df)
    .mark_line(opacity=0.65, strokeCap="round")
    .encode(
        longitude=alt.Longitude("lon", type="quantitative"),
        latitude=alt.Latitude("lat", type="quantitative"),
        detail=alt.Detail("flow_id", type="nominal"),
        order=alt.Order("order", type="ordinal"),
        strokeWidth=alt.StrokeWidth("stroke_width", type="quantitative", scale=None, legend=None),
        color=alt.Color(
            FLOW.translate(ESCAPE),
            type="quantitative",
            title=FLOW,
            scale=alt.Scale(
                domain=[flow_min + p * (flow_max - flow_min) for p, _ in SEQ_MARKS],
                range=[c for _, c in SEQ_MARKS],
                interpolate="rgb",
            ),
            legend=alt.Legend(orient="bottom-right", offset=10, format=",.0f"),
        ),
        tooltip=[
            alt.Tooltip(ORIGIN.translate(ESCAPE), type="nominal", title=ORIGIN),
            alt.Tooltip(DEST.translate(ESCAPE), type="nominal", title=DEST),
            alt.Tooltip(FLOW.translate(ESCAPE), type="quantitative", title=FLOW, format=",.0f"),
        ],
    )
    .project(**proj)
)

points = (
    alt.Chart(cities_df)
    .mark_circle(size=150, color=IMPRINT_PALETTE[0], stroke=PAGE_BG, strokeWidth=2)
    .encode(
        longitude=alt.Longitude("lon", type="quantitative"),
        latitude=alt.Latitude("lat", type="quantitative"),
        tooltip=[alt.Tooltip("city", type="nominal", title="City")],
    )
    .project(**proj)
)

# Each label is drawn twice: a page-colored halo underneath separates the letters from the arcs
label_layers = [
    alt.Chart(group)
    .mark_text(fontSize=12, fontWeight="bold", color=INK, dx=dx, dy=dy, **halo)
    .encode(
        longitude=alt.Longitude("lon", type="quantitative"),
        latitude=alt.Latitude("lat", type="quantitative"),
        text=alt.Text("city", type="nominal"),
    )
    .project(**proj)
    for halo in ({"stroke": PAGE_BG, "strokeWidth": 4, "strokeJoin": "round"}, {})
    for (dx, dy), group in cities_df.groupby(["dx", "dy"])
]

chart = (
    alt.layer(base, arcs, points, *label_layers)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title("flowmap-origin-destination · python · altair · anyplot.ai", fontSize=16, anchor="start"),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=12,
        titleFontSize=14,
        gradientLength=160,
        padding=8,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
