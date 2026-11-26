"""anyplot.ai
contour-map-geographic: Contour Lines on Geographic Map
Library: altair 6.1.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-20
"""

import os
import sys


# Prevent altair.py (this file) from shadowing the installed altair package
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p and os.path.abspath(p) != _script_dir]

import altair as alt
import numpy as np
import pandas as pd
from contourpy import contour_generator
from PIL import Image


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BASEMAP_STROKE = "#888880" if THEME == "light" else "#666660"

# Imprint palette (categorical, all eight positions)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint diverging ramp for fields, cold blue -> page-colored midpoint -> warm red
DIV_FIELDS_RANGE = ["#4467A3", PAGE_BG, "#AE3030"]

# Constants
MILD = 15  # temperature (°C) where the diverging ramp has its midpoint
CONTOUR_STEP = 5  # isoline interval in °C

# Columns: set these to your table's column names
LONGITUDE = "longitude"  # role: lon
LATITUDE = "latitude"  # role: lat
TEMPERATURE = "Temperature (°C)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("grid.csv")
# Latitudes are spaced evenly in Mercator y so the projected raster has no stripes
np.random.seed(42)
_y_lo = np.log(np.tan(np.pi / 4 + 30 * np.pi / 360))
_y_hi = np.log(np.tan(np.pi / 4 + 72 * np.pi / 360))
_lats = 2 * (np.arctan(np.exp(np.linspace(_y_lo, _y_hi, 110))) - np.pi / 4) * 180 / np.pi
_lons = np.linspace(-25, 55, 160)
_lon_grid, _lat_grid = np.meshgrid(_lons, _lats)
_temp = (
    30
    - 0.6 * (_lat_grid - 30)
    + 3 * np.sin((_lon_grid + 10) / 15)
    + 2 * np.cos(_lat_grid / 10)
    - 5 * np.exp(-((_lat_grid - 47) ** 2 + (_lon_grid - 10) ** 2) / 100)
    - 3 * np.exp(-((_lat_grid - 65) ** 2 + (_lon_grid - 25) ** 2) / 150)
    + np.random.normal(0, 0.04, _lon_grid.shape)
)
df = pd.DataFrame(
    {LONGITUDE: _lon_grid.flatten(), LATITUDE: _lat_grid.flatten(), TEMPERATURE: np.clip(_temp, -15, 35).flatten()}
)

# Plot
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
lon_axis = np.sort(df[LONGITUDE].unique())
lat_axis = np.sort(df[LATITUDE].unique())
grid = df.pivot_table(index=LATITUDE, columns=LONGITUDE, values=TEMPERATURE).to_numpy()
t_lo, t_hi = df[TEMPERATURE].min(), df[TEMPERATURE].max()

# True isolines from contourpy, one polyline per segment
levels = np.arange(np.ceil(t_lo / CONTOUR_STEP) * CONTOUR_STEP, t_hi, CONTOUR_STEP)
gen = contour_generator(x=lon_axis, y=lat_axis, z=grid)
line_rows = []
seg_id = 0
for level in levels:
    for seg in gen.lines(level):
        if len(seg) >= 3:
            for order, (lon, lat) in enumerate(seg):
                line_rows.append(
                    {LONGITUDE: float(lon), LATITUDE: float(lat), "level": float(level), "seg": seg_id, "order": order}
                )
            seg_id += 1
line_df = pd.DataFrame(line_rows).sort_values(["seg", "order"])

# Value labels: per level, the line points nearest to a few reference meridians inside the map window
lon_mid = df[LONGITUDE].median()
lon_span = df[LONGITUDE].max() - df[LONGITUDE].min()
lat_lo, lat_hi = df[LATITUDE].min() + 8, df[LATITUDE].max() - 8
label_rows = []
for level in levels:
    pts = line_df[(line_df["level"] == level) & line_df[LATITUDE].between(lat_lo, lat_hi)]
    for anchor in (lon_mid - 0.2 * lon_span, lon_mid + 0.1 * lon_span):
        if len(pts) > 0:
            row = pts.loc[(pts[LONGITUDE] - anchor).abs().idxmin()]
            label_rows.append({LONGITUDE: row[LONGITUDE], LATITUDE: row[LATITUDE], "label": f"{level:.0f}°"})
label_df = pd.DataFrame(label_rows)

# Chart
W, H = 800, 450
proj = {"type": "mercator", "scale": 560, "center": [15, 52]}
countries = alt.topo_feature("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json", "countries")

heat = (
    alt.Chart(df)
    .mark_square(size=100, strokeWidth=0)
    .encode(
        longitude=alt.Longitude(LONGITUDE.translate(ESCAPE), type="quantitative"),
        latitude=alt.Latitude(LATITUDE.translate(ESCAPE), type="quantitative"),
        color=alt.Color(
            TEMPERATURE.translate(ESCAPE),
            type="quantitative",
            title=TEMPERATURE,
            scale=alt.Scale(
                domain=[float(min(t_lo, MILD - 1)), MILD, float(max(t_hi, MILD + 1))],
                range=DIV_FIELDS_RANGE,
                interpolate="rgb",
            ),
            legend=alt.Legend(
                titleFontSize=12,
                labelFontSize=12,
                titlePadding=8,
                gradientLength=220,
                gradientThickness=18,
                orient="right",
            ),
        ),
        tooltip=[
            alt.Tooltip(LONGITUDE.translate(ESCAPE), type="quantitative", title="Longitude", format=".1f"),
            alt.Tooltip(LATITUDE.translate(ESCAPE), type="quantitative", title="Latitude", format=".1f"),
            alt.Tooltip(TEMPERATURE.translate(ESCAPE), type="quantitative", title=TEMPERATURE, format=".1f"),
        ],
    )
    .project(**proj)
)

borders = alt.Chart(countries).mark_geoshape(filled=False, stroke=BASEMAP_STROKE, strokeWidth=0.8).project(**proj)

isolines = (
    alt.Chart(line_df)
    .mark_line(color=INK, strokeWidth=1.4, opacity=0.8)
    .encode(
        longitude=alt.Longitude(LONGITUDE.translate(ESCAPE), type="quantitative"),
        latitude=alt.Latitude(LATITUDE.translate(ESCAPE), type="quantitative"),
        detail=alt.Detail("seg", type="nominal"),
        order=alt.Order("order", type="quantitative"),
    )
    .project(**proj)
)

label_base = (
    alt.Chart(label_df)
    .encode(
        longitude=alt.Longitude(LONGITUDE.translate(ESCAPE), type="quantitative"),
        latitude=alt.Latitude(LATITUDE.translate(ESCAPE), type="quantitative"),
        text=alt.Text("label", type="nominal"),
    )
    .project(**proj)
)
# Halo layer under a plain fill layer keeps the glyphs crisp
label_halo = label_base.mark_text(fontSize=14, fontWeight="bold", color=PAGE_BG, stroke=PAGE_BG, strokeWidth=2.5)
label_text = label_base.mark_text(fontSize=14, fontWeight="bold", color=INK)

chart = (
    alt.layer(heat, borders, isolines, label_halo, label_text)
    .properties(
        width=W,
        height=H,
        padding=10,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        background=PAGE_BG,
        title=alt.Title("contour-map-geographic · python · altair · anyplot.ai", fontSize=16, anchor="middle"),
    )
    .configure_view(fill=PAGE_BG, stroke=INK_SOFT, strokeWidth=0.5)
    .configure_title(color=INK)
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK)
)

# Save
TW, TH = 3200, 1800
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (TW, TH):
    _scale = min(1.0, TW / _img.width, TH / _img.height)
    _img = _img.resize((round(_img.width * _scale), round(_img.height * _scale)), Image.LANCZOS)
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _img.width) // 2, (TH - _img.height) // 2))
    _canvas.save(f"plot-{THEME}.png")

chart.save(f"plot-{THEME}.html")
