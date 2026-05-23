""" anyplot.ai
map-marker-clustered: Clustered Marker Map
Library: altair 6.1.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-23
"""

import os
import sys


# Remove this script's own directory from sys.path to avoid shadowing the installed altair package
sys.path = [p for p in sys.path if p not in ("", os.path.dirname(os.path.abspath(__file__)))]

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
MAP_FILL = "#E8E6DF" if THEME == "light" else "#2A2A27"
MAP_STROKE = "#B8B7B0" if THEME == "light" else "#4A4A44"

ANYPLOT_PALETTE = ["#009E73", "#9418DB", "#B71D27", "#16B8F3", "#99B314", "#D359A7", "#BA843E"]

# Data — store locations across the United States
np.random.seed(42)

cities = [
    (40.7128, -74.0060, "New York", "retail"),
    (34.0522, -118.2437, "Los Angeles", "retail"),
    (41.8781, -87.6298, "Chicago", "food"),
    (29.7604, -95.3698, "Houston", "food"),
    (33.4484, -112.0740, "Phoenix", "services"),
    (39.7392, -104.9903, "Denver", "services"),
    (47.6062, -122.3321, "Seattle", "retail"),
    (25.7617, -80.1918, "Miami", "food"),
    (42.3601, -71.0589, "Boston", "retail"),
    (38.9072, -77.0369, "Washington DC", "services"),
]

n_points = 500
lats, lons, store_labels, cats = [], [], [], []
for i in range(n_points):
    city = cities[i % len(cities)]
    lats.append(city[0] + np.random.normal(0, 1.5))
    lons.append(city[1] + np.random.normal(0, 1.5))
    store_labels.append(f"Store {i + 1}")
    cats.append(city[3])

df = pd.DataFrame({"lat": lats, "lon": lons, "label": store_labels, "category": cats})

# Grid-based clustering — no external dependencies beyond numpy/pandas
grid_size = 2.5  # degrees
df["lat_bin"] = (df["lat"] / grid_size).round() * grid_size
df["lon_bin"] = (df["lon"] / grid_size).round() * grid_size

cluster_summary = (
    df.groupby(["lat_bin", "lon_bin"])
    .agg(
        lat=("lat", "mean"),
        lon=("lon", "mean"),
        count=("label", "count"),
        dominant_category=("category", lambda x: x.mode().iloc[0]),
    )
    .reset_index()
)
cluster_summary["marker_size"] = np.log1p(cluster_summary["count"]) * 150 + 100

# US states basemap (Vega CDN)
us_10m_url = "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/us-10m.json"
states = alt.topo_feature(us_10m_url, "states")

background = (
    alt.Chart(states)
    .mark_geoshape(fill=MAP_FILL, stroke=MAP_STROKE, strokeWidth=0.5)
    .project(type="albersUsa")
    .properties(width=620, height=320)
)

category_colors = alt.Scale(
    domain=["retail", "food", "services"], range=[ANYPLOT_PALETTE[0], ANYPLOT_PALETTE[1], ANYPLOT_PALETTE[2]]
)

clusters = (
    alt.Chart(cluster_summary)
    .mark_circle(opacity=0.85, stroke=PAGE_BG, strokeWidth=1.5)
    .encode(
        longitude="lon:Q",
        latitude="lat:Q",
        size=alt.Size("marker_size:Q", scale=alt.Scale(range=[200, 2000]), legend=None),
        color=alt.Color("dominant_category:N", scale=category_colors, title="Category"),
        tooltip=[
            alt.Tooltip("count:Q", title="Locations"),
            alt.Tooltip("dominant_category:N", title="Type"),
            alt.Tooltip("lat:Q", title="Latitude", format=".2f"),
            alt.Tooltip("lon:Q", title="Longitude", format=".2f"),
        ],
    )
    .project(type="albersUsa")
)

# Count labels — near-white text is readable on all anyplot palette marker colors
count_labels = (
    alt.Chart(cluster_summary[cluster_summary["count"] > 1])
    .mark_text(fontSize=10, fontWeight="bold", color="#FFFDF6")
    .encode(longitude="lon:Q", latitude="lat:Q", text="count:Q")
    .project(type="albersUsa")
)

TITLE = "map-marker-clustered · python · altair · anyplot.ai"

chart = (
    (background + clusters + count_labels)
    .properties(
        background=PAGE_BG,
        title=alt.Title(
            text=TITLE,
            subtitle="500 US store locations clustered by proximity (size = count)",
            fontSize=16,
            subtitleFontSize=12,
            color=INK,
            subtitleColor=INK_SOFT,
            anchor="start",
        ),
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=10,
        titleFontSize=10,
        symbolSize=150,
        orient="bottom-right",
    )
)

# Save PNG then pad to exact 3200×1800 target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        "Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

# Save HTML
chart.save(f"plot-{THEME}.html")
