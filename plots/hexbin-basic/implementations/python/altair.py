""" anyplot.ai
hexbin-basic: Basic Hexbin Plot
Library: altair 6.3.0 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-27
"""

import os

import altair as alt
import numpy as np
import pandas as pd
from PIL import Image


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (first position is the brand green)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for filled cells (fields), as (position, hex) stops, low -> high
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# Constants
HEX_ACROSS = 30  # hexagons across the width of the plotting area (bin resolution)
VIEW_W, VIEW_H = 640, 340  # approximate plotting-area size in px, used to keep hexagons regular on screen
HEX_PATH = "M0,-1L0.866,-0.5L0.866,0.5L0,1L-0.866,0.5L-0.866,-0.5Z"  # pointy-top hexagon outline

# Columns: set these to your table's column names
LONGITUDE = "Longitude (°E)"  # role: x
LATITUDE = "Latitude (°N)"  # role: y
COUNT = "Observations per hexagon (log scale)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("gps.csv")
# GPS coordinates showing traffic density in Seattle
np.random.seed(42)
n_points = 5000

# Downtown core - highest density (tight cluster)
downtown_lon = np.random.randn(n_points // 2) * 0.006 + (-122.335)
downtown_lat = np.random.randn(n_points // 2) * 0.005 + 47.608

# Shopping district - secondary hotspot
shopping_lon = np.random.randn(n_points // 3) * 0.005 + (-122.315)
shopping_lat = np.random.randn(n_points // 3) * 0.004 + 47.622

# Industrial zone - increased spread to avoid misleading bright center
industrial_lon = np.random.randn(n_points // 6) * 0.007 + (-122.355)
industrial_lat = np.random.randn(n_points // 6) * 0.005 + 47.635

df = pd.DataFrame(
    {
        LONGITUDE: np.concatenate([downtown_lon, shopping_lon, industrial_lon]),
        LATITUDE: np.concatenate([downtown_lat, shopping_lat, industrial_lat]),
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})

# Axis domains with a margin of one hexagon around the data
lon_min, lon_max = df[LONGITUDE].min(), df[LONGITUDE].max()
lat_min, lat_max = df[LATITUDE].min(), df[LATITUDE].max()
hex_w_px = VIEW_W / HEX_ACROSS  # flat width of one hexagon in px
hex_r_px = hex_w_px / np.sqrt(3)  # center-to-corner radius in px
x_pad = 1.5 * (lon_max - lon_min) / HEX_ACROSS
lon_lo, lon_hi = lon_min - x_pad, lon_max + x_pad
lat_pad = 1.5 * hex_r_px * (lat_max - lat_min) / VIEW_H
lat_lo, lat_hi = lat_min - lat_pad, lat_max + lat_pad

# Hexagonal binning in screen space so every hexagon is regular on screen
valid = df[[LONGITUDE, LATITUDE]].dropna()  # a missing coordinate cannot fall in any hexagon
px = (valid[LONGITUDE] - lon_lo) / (lon_hi - lon_lo) * VIEW_W
py = (valid[LATITUDE] - lat_lo) / (lat_hi - lat_lo) * VIEW_H
row = np.round(py / (1.5 * hex_r_px)).astype(int)
shift = (row % 2) * 0.5
col = np.round(px / hex_w_px - shift).astype(int)
hexbins = (
    pd.DataFrame({"col": col, "row": row, "shift": shift})
    .groupby(["col", "row", "shift"])
    .size()
    .reset_index(name=COUNT)
)
hexbins[LONGITUDE] = lon_lo + (hexbins["col"] + hexbins["shift"]) * hex_w_px / VIEW_W * (lon_hi - lon_lo)
hexbins[LATITUDE] = lat_lo + hexbins["row"] * 1.5 * hex_r_px / VIEW_H * (lat_hi - lat_lo)

# Symlog color scale: one domain value per ramp stop, spaced by position in log space
lo, hi = hexbins[COUNT].min(), hexbins[COUNT].max()
log_lo, log_hi = np.log1p(lo), np.log1p(hi)
color_domain = [float(np.expm1(log_lo + p * (log_hi - log_lo))) for p, _ in SEQ_FIELDS]

# Marker area in px^2: the symbol path spans +-1, so a hexagon of flat width hex_w_px
# fills a square of side hex_w_px * 2 / sqrt(3) * ... (calibrated by render)
hex_area = (hex_r_px * 2) ** 2

chart = (
    alt.Chart(hexbins)
    .mark_point(shape=HEX_PATH, filled=True, stroke=PAGE_BG, strokeWidth=0.6, opacity=1)
    .encode(
        x=alt.X(
            LONGITUDE.translate(ESCAPE),
            type="quantitative",
            title=LONGITUDE,
            scale=alt.Scale(domain=[lon_lo, lon_hi], nice=False),
            axis=alt.Axis(format=".2f", tickCount=6),
        ),
        y=alt.Y(
            LATITUDE.translate(ESCAPE),
            type="quantitative",
            title=LATITUDE,
            scale=alt.Scale(domain=[lat_lo, lat_hi], nice=False),
            axis=alt.Axis(format=".2f", tickCount=6),
        ),
        color=alt.Color(
            COUNT.translate(ESCAPE),
            type="quantitative",
            title="Points per hexagon (log)",
            scale=alt.Scale(type="symlog", domain=color_domain, range=[c for _, c in SEQ_FIELDS], interpolate="rgb"),
            legend=alt.Legend(
                titleFontSize=10, labelFontSize=10, gradientLength=140, gradientThickness=16, titleLimit=140
            ),
        ),
        size=alt.value(hex_area),
        tooltip=[
            alt.Tooltip(LONGITUDE.translate(ESCAPE), type="quantitative", title=LONGITUDE, format=".4f"),
            alt.Tooltip(LATITUDE.translate(ESCAPE), type="quantitative", title=LATITUDE, format=".4f"),
            alt.Tooltip(COUNT.translate(ESCAPE), type="quantitative", title="Points"),
        ],
    )
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title("hexbin-basic · python · altair · anyplot.ai", fontSize=16, anchor="middle", color=INK),
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.12,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=11,
        titleFontSize=13,
    )
    .configure_legend(fillColor=ELEVATED_BG, strokeColor=INK_SOFT, labelColor=INK_SOFT, titleColor=INK, padding=8)
    .configure_title(color=INK)
)

# Save
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
