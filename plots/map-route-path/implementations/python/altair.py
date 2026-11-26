"""anyplot.ai
map-route-path: Route Path Map
Library: altair 6.3.0 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os
import sys


sys.path.pop(0)  # prevent local altair.py from shadowing the library
import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MAP_FILL = "#DEDAD4" if THEME == "light" else "#2C2C28"
MAP_STROKE = "#B0AAA0" if THEME == "light" else "#4A4A42"

# Imprint palette (route line = position 1, end marker = position 2)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for marks drawn on the page, as (position, hex) stops
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)

# Column constants
LATITUDE = "Latitude"  # role: lat
LONGITUDE = "Longitude"  # role: lon
SEQUENCE = "Sequence"  # role: sequence
ELEVATION = "Elevation (m)"  # role: extra
PLACE = "Place"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("route.csv")
# Route 66, Chicago to Los Angeles: 8 segments, ~160 synthetic waypoints
np.random.seed(42)
cities = [
    ("Chicago", 41.85, -87.65, 180),
    ("Springfield", 39.80, -89.65, 165),
    ("St. Louis", 38.63, -90.20, 130),
    ("Joplin", 37.08, -94.52, 290),
    ("Oklahoma City", 35.47, -97.52, 365),
    ("Amarillo", 35.22, -101.83, 1100),
    ("Albuquerque", 35.08, -106.65, 1510),
    ("Flagstaff", 35.20, -111.65, 2100),
    ("Los Angeles", 34.05, -118.25, 95),
]
steps = 20
t_vals = np.linspace(0, 1, steps, endpoint=False)
lat_parts, lon_parts, elev_parts, place_parts = [], [], [], []
for (name, lat1, lon1, el1), (_, lat2, lon2, el2) in zip(cities[:-1], cities[1:], strict=True):
    lat_parts.append(lat1 + (lat2 - lat1) * t_vals + np.random.normal(0, 0.07, steps))
    lon_parts.append(lon1 + (lon2 - lon1) * t_vals + np.random.normal(0, 0.07, steps))
    elev_parts.append(el1 + (el2 - el1) * t_vals)
    place_parts.append([name] + [None] * (steps - 1))
lat_parts.append(np.array([cities[-1][1]]))
lon_parts.append(np.array([cities[-1][2]]))
elev_parts.append(np.array([cities[-1][3]]))
place_parts.append([cities[-1][0]])
elevation = np.concatenate(elev_parts)
df = pd.DataFrame(
    {
        LATITUDE: np.concatenate(lat_parts),
        LONGITUDE: np.concatenate(lon_parts),
        SEQUENCE: np.arange(len(elevation)),
        ELEVATION: elevation,
        PLACE: [p for part in place_parts for p in part],
    }
)
df[ELEVATION] = df[ELEVATION] + np.random.normal(0, 45, len(df))

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
LAT, LON, SEQ, ELEV = (c.translate(ESCAPE) for c in (LATITUDE, LONGITUDE, SEQUENCE, ELEVATION))

start_df = df.iloc[[0]]
end_df = df.iloc[[-1]]
peak_df = df.loc[[df[ELEVATION].idxmax()]].assign(label=lambda d: [f"▲ Highest point {d[ELEVATION].iloc[0]:.0f} m"])
start_df = start_df.assign(label=f"Start: {start_df[PLACE].iloc[0]}")
end_df = end_df.assign(label=f"End: {end_df[PLACE].iloc[0]}")
dot_df = df.iloc[::4]

title_str = "Route 66 Road Trip · map-route-path · python · altair · anyplot.ai"

lo, hi = df[ELEVATION].min(), df[ELEVATION].max()
elevation_scale = alt.Scale(
    domain=[lo + p * (hi - lo) for p, _ in SEQ_MARKS], range=[c for _, c in SEQ_MARKS], interpolate="rgb"
)

# Basemap: US states (CDN topojson)
states = alt.topo_feature("https://cdn.jsdelivr.net/npm/vega-datasets@2/data/us-10m.json", "states")
geo = {"longitude": alt.Longitude(LON, type="quantitative"), "latitude": alt.Latitude(LAT, type="quantitative")}

# Projection fitted to the route: centered on its extent, scaled so the route spans ~72% of the width
lon_mid = (df[LONGITUDE].max() + df[LONGITUDE].min()) / 2
lat_mid = (df[LATITUDE].max() + df[LATITUDE].min()) / 2
lon_span = np.radians(df[LONGITUDE].max() - df[LONGITUDE].min()) * np.cos(np.radians(lat_mid))
PROJ = {
    "type": "albers",
    "rotate": [-lon_mid, 0],
    "center": [0, lat_mid],
    "parallels": [df[LATITUDE].min(), df[LATITUDE].max()],
    "scale": float(0.72 * 800 / lon_span),
}

background = (
    alt.Chart(states).mark_geoshape(fill=MAP_FILL, stroke=MAP_STROKE, strokeWidth=0.6, clip=True).project(**PROJ)
)

route_line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3.5, color=IMPRINT_PALETTE[0], strokeCap="round")
    .encode(
        **geo,
        order=alt.Order(SEQ, type="quantitative"),
        tooltip=[
            alt.Tooltip(LAT, type="quantitative", title=LATITUDE, format=".2f"),
            alt.Tooltip(LON, type="quantitative", title=LONGITUDE, format=".2f"),
            alt.Tooltip(ELEV, type="quantitative", title=ELEVATION, format=".0f"),
        ],
    )
    .project(**PROJ)
)

elevation_dots = (
    alt.Chart(dot_df)
    .mark_circle(size=42, opacity=0.95, stroke=PAGE_BG, strokeWidth=0.6)
    .encode(
        **geo,
        color=alt.Color(
            ELEV,
            type="quantitative",
            title=ELEVATION,
            scale=elevation_scale,
            legend=alt.Legend(
                titleFontSize=13,
                labelFontSize=12,
                gradientLength=200,
                gradientThickness=14,
                orient="bottom-left",
                offset=10,
            ),
        ),
        tooltip=[alt.Tooltip(ELEV, type="quantitative", title=ELEVATION, format=".0f")],
    )
    .project(**PROJ)
)

start_marker = (
    alt.Chart(start_df)
    .mark_point(
        shape="circle", size=420, filled=True, opacity=1, color=IMPRINT_PALETTE[0], stroke=PAGE_BG, strokeWidth=2.5
    )
    .encode(**geo, tooltip=alt.Tooltip("label", type="nominal", title="Start"))
    .project(**PROJ)
)

end_marker = (
    alt.Chart(end_df)
    .mark_point(
        shape="square", size=420, filled=True, opacity=1, color=IMPRINT_PALETTE[1], stroke=PAGE_BG, strokeWidth=2.5
    )
    .encode(**geo, tooltip=alt.Tooltip("label", type="nominal", title="End"))
    .project(**PROJ)
)

# Labels: one layer each, because every label needs its own alignment to stay clear of the others
start_label = (
    alt.Chart(start_df)
    .mark_text(fontSize=13, fontWeight="bold", dy=-20, baseline="bottom", align="center", color=INK)
    .encode(**geo, text=alt.Text(PLACE, type="nominal"))
    .project(**PROJ)
)

end_label = (
    alt.Chart(end_df)
    .mark_text(fontSize=13, fontWeight="bold", dy=-20, baseline="bottom", align="left", color=INK)
    .encode(**geo, text=alt.Text(PLACE, type="nominal"))
    .project(**PROJ)
)

peak_label = (
    alt.Chart(peak_df)
    .mark_text(fontSize=12, fontWeight="bold", dy=-30, dx=6, baseline="bottom", align="left", color=INK)
    .encode(**geo, text=alt.Text("label", type="nominal"))
    .project(**PROJ)
)

chart = (
    alt.layer(background, route_line, elevation_dots, start_marker, end_marker, start_label, end_label, peak_label)
    .properties(
        width=800,
        height=450,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        background=PAGE_BG,
        title=alt.Title(text=title_str, fontSize=16, anchor="start", color=INK, offset=8),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
)

# Save PNG + HTML
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")
