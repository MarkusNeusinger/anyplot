""" anyplot.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: altair 6.3.0 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-26
"""

import os
import sys
from collections import Counter


# Work around filename shadowing the altair library: drop this directory from the import path
_here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _here]

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
LAND_FILL = "#E8E4DC" if THEME == "light" else "#2C2C28"
LAND_STROKE = "#B0AFA8" if THEME == "light" else "#4A4A44"

# Imprint sequential ramp for colored fields (hexagon cells fill the map), as (position, hex) stops
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
)

# Columns
LAT = "lat"  # role: lat
LON = "lon"  # role: lon
SIGHTINGS = "Sightings"  # statistic drawn per cell (count of points)

# Data: bird species sightings — deliberately wide density spread to showcase log-scale range
np.random.seed(42)
# (lat, lon, n_obs, spread_deg) — from sparse (150) to heavy (2500)
clusters = [
    (47.6, -122.3, 2000, 0.45),  # Seattle / Pacific flyway (dense hub)
    (37.8, -122.4, 800, 0.40),  # San Francisco Bay (moderate)
    (29.8, -95.4, 350, 0.40),  # Houston / Gulf Coast (lighter)
    (41.9, -87.6, 1500, 0.45),  # Chicago / Great Lakes (dense hub)
    (40.7, -74.0, 2500, 0.40),  # New York metro (densest hub)
    (38.9, -77.0, 500, 0.38),  # Washington DC (moderate)
    (25.8, -80.2, 150, 0.38),  # Miami / Atlantic flyway (sparse)
    (44.9, -93.2, 250, 0.42),  # Minneapolis / Mississippi corridor (sparse)
]

lats_all, lons_all = [], []
for clat, clon, n, spread in clusters:
    lats_all.extend(np.random.normal(clat, spread, n))
    lons_all.extend(np.random.normal(clon, spread, n))

df = pd.DataFrame({LAT: np.clip(np.array(lats_all), 24.0, 50.0), LON: np.clip(np.array(lons_all), -126.0, -65.0)})

# Plot
lats = df[LAT].to_numpy()
lons = df[LON].to_numpy()

# Flat-top hexagonal binning in lat/lon space
HEX_R = 0.65  # degrees (~65 km at mid-latitudes)
COL_STEP = 1.5 * HEX_R
ROW_STEP = HEX_R * np.sqrt(3)

cols = np.round(lons / COL_STEP).astype(int)
row_off = (np.abs(cols) % 2) * 0.5
rows = np.round(lats / ROW_STEP - row_off).astype(int)
hex_counts = Counter(zip(cols.tolist(), rows.tolist(), strict=False))

features = []
for (c, r), count in hex_counts.items():
    lon_c = c * COL_STEP
    lat_c = (r + (abs(c) % 2) * 0.5) * ROW_STEP
    # Clockwise winding in geographic coords → renders as filled interior
    # (vl-convert flips y-axis; CW geo = CCW screen = D3 interior fill)
    verts = [
        [lon_c + HEX_R * np.cos(np.radians(-60 * i)), lat_c + HEX_R * np.sin(np.radians(-60 * i))] for i in range(6)
    ]
    verts.append(verts[0])
    features.append(
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [verts]},
            "properties": {SIGHTINGS: int(count)},
        }
    )

# Labels for the three strongest migration hubs — guide viewer to the story
ann_data = [
    {LON: -75.2, LAT: 41.6, "label": "NYC Metro"},
    {LON: -122.3, LAT: 47.0, "label": "Seattle"},
    {LON: -87.6, LAT: 42.5, "label": "Chicago"},
]

# Base map — vega CDN, no local package required
WORLD_URL = "https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/world-110m.json"
# Mercator projection centred on continental US, tuned to fit inner 620×320 view
proj_params = {"type": "mercator", "scale": 600, "center": [-97.5, 37]}

basemap = (
    alt.Chart(alt.topo_feature(WORLD_URL, "land"))
    .mark_geoshape(fill=LAND_FILL, stroke=LAND_STROKE, strokeWidth=0.5)
    .project(**proj_params)
)

counts = [f["properties"][SIGHTINGS] for f in features]
c_lo, c_hi = min(counts), max(counts)

# Hexbin layer — inline GeoJSON features, sequential colormap brand-green → blue
hexbin = (
    alt.Chart(alt.InlineData(values=features, format=alt.DataFormat(type="json")))
    .mark_geoshape(stroke=PAGE_BG, strokeWidth=0.3, opacity=0.85)
    .encode(
        color=alt.Color(
            f"properties.{SIGHTINGS}",
            type="quantitative",
            title=SIGHTINGS,
            # Log scale; the stops sit at their ramp positions in log space
            scale=alt.Scale(
                type="log",
                domain=[c_lo * (c_hi / c_lo) ** p for p, _ in SEQ_FIELDS],
                range=[c for _, c in SEQ_FIELDS],
                interpolate="rgb",
            ),
            legend=alt.Legend(
                title=SIGHTINGS, gradientLength=220, gradientThickness=16, labelFontSize=12, titleFontSize=13
            ),
        ),
        tooltip=[alt.Tooltip(f"properties.{SIGHTINGS}", type="quantitative", title=SIGHTINGS)],
    )
    .project(**proj_params)
)

# Text annotations directing the viewer to the densest migration hubs
annotation = (
    alt.Chart(alt.InlineData(values=ann_data))
    .mark_text(color=INK, fontSize=11, fontWeight="bold", align="right", dy=-4)
    .encode(longitude=f"{LON}:Q", latitude=f"{LAT}:Q", text="label:N")
    .project(**proj_params)
)

chart = (
    alt.layer(basemap, hexbin, annotation)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title("US Bird Migration Hotspots · hexbin-map-geographic · python · altair · anyplot.ai"),
    )
    .configure_title(color=INK, fontSize=16, fontWeight="bold")
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=12,
        titleFontSize=13,
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)

TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
