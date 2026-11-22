"""anyplot.ai
bubble-map-geographic: Bubble Map with Sized Geographic Markers
Library: altair 6.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os
import sys

import pandas as pd
from PIL import Image


# Work around filename shadowing the altair library
sys.path.pop(0)
import altair as alt


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
LAND_FILL = "#E8E4DC" if THEME == "light" else "#2C2C28"
LAND_STROKE = "#B0AFA8" if THEME == "light" else "#4A4A44"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
LOCATION = "Location"  # role: label
LATITUDE = "Latitude"  # role: latitude
LONGITUDE = "Longitude"  # role: longitude
MAGNITUDE = "Magnitude (Mw)"  # role: value
REGION = "Tectonic region"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("events.csv")
# Major earthquakes (M >= 6.0), 20th-21st century, after the USGS Significant Earthquake Catalog
df = pd.DataFrame(
    {
        LOCATION: [
            "Tōhoku, Japan",
            "Sumatra-Andaman",
            "Hokkaido, Japan",
            "Java, Indonesia",
            "Solomon Islands",
            "Kuril Islands",
            "Sea of Okhotsk",
            "Christchurch, NZ",
            "Tonga",
            "Kamchatka, Russia",
            "Valdivia, Chile",
            "Bio-Bio, Chile",
            "Michoacan, Mexico",
            "Haiti",
            "Ecuador",
            "Bolivia (deep)",
            "Peru",
            "El Salvador",
            "Costa Rica",
            "Alaska",
            "Turkey-Syria",
            "Izmit, Turkey",
            "Zagros, Iran",
            "Bam, Iran",
            "Nepal",
            "Gujarat, India",
            "Pakistan (AJK)",
            "Hindu Kush",
            "Sichuan, China",
            "Yunnan, China",
        ],
        LATITUDE: [
            38.3,
            3.3,
            42.16,
            -9.35,
            -8.47,
            46.55,
            54.89,
            -43.58,
            -18.0,
            52.75,
            -38.14,
            -35.9,
            18.19,
            18.44,
            0.36,
            -13.84,
            -5.76,
            13.04,
            10.39,
            61.0,
            37.22,
            40.75,
            26.75,
            29.00,
            28.15,
            23.36,
            34.55,
            36.07,
            31.00,
            25.07,
        ],
        LONGITUDE: [
            142.37,
            95.98,
            142.86,
            107.35,
            157.04,
            153.30,
            153.28,
            172.68,
            -174.0,
            159.5,
            -73.41,
            -72.73,
            -102.53,
            -72.57,
            -79.94,
            -67.55,
            -75.27,
            -88.66,
            -85.24,
            -147.5,
            37.02,
            29.99,
            57.6,
            58.37,
            84.71,
            70.34,
            73.59,
            70.49,
            103.32,
            99.31,
        ],
        MAGNITUDE: [
            9.1,
            9.1,
            8.3,
            7.7,
            8.1,
            8.3,
            8.3,
            6.3,
            7.4,
            9.0,
            9.5,
            8.8,
            8.0,
            7.0,
            7.8,
            8.2,
            8.0,
            7.7,
            7.6,
            9.2,
            7.8,
            7.6,
            6.8,
            6.6,
            7.8,
            7.7,
            7.6,
            6.1,
            7.9,
            6.2,
        ],
        REGION: ["East & SE Asia"] * 10 + ["Americas"] * 10 + ["Middle East & C. Asia"] * 4 + ["South Asia"] * 6,
    }
)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
TITLE = "Major Earthquakes · bubble-map-geographic · python · altair · anyplot.ai"
VIEW_W, VIEW_H = 620, 320
PROJECTION = {"type": "equirectangular", "scale": VIEW_W / 6.4, "translate": [VIEW_W / 2, VIEW_H / 2]}

# World map basemap via vega-datasets CDN (no local package required)
world_url = "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/world-110m.json"
countries = alt.topo_feature(world_url, "countries")

# Base map layer: country boundaries, quieter than the bubbles
base_map = (
    alt.Chart(countries)
    .mark_geoshape(fill=LAND_FILL, stroke=LAND_STROKE, strokeWidth=0.4)
    .project(**PROJECTION)
    .properties(width=VIEW_W, height=VIEW_H)
)

# Bubble layer: area (Vega-Lite size) scales with magnitude; largest drawn first so small ones stay on top
bubbles = (
    alt.Chart(df.sort_values(MAGNITUDE, ascending=False))
    .mark_circle(opacity=0.65, stroke=PAGE_BG, strokeWidth=0.6)
    .encode(
        longitude=alt.Longitude(LONGITUDE.translate(ESCAPE), type="quantitative"),
        latitude=alt.Latitude(LATITUDE.translate(ESCAPE), type="quantitative"),
        size=alt.Size(
            MAGNITUDE.translate(ESCAPE),
            type="quantitative",
            title=MAGNITUDE,
            scale=alt.Scale(
                domain=[df[MAGNITUDE].min() - 0.1, df[MAGNITUDE].max()], range=[12, 420], type="linear", zero=False
            ),
            legend=alt.Legend(
                orient="bottom-left", offset=6, values=[6.5, 7.5, 8.5, 9.5], symbolFillColor=IMPRINT_PALETTE[0]
            ),
        ),
        color=alt.Color(
            REGION.translate(ESCAPE),
            type="nominal",
            title=REGION,
            sort=None,
            scale=alt.Scale(domain=list(df[REGION].unique()), range=IMPRINT_PALETTE),
            legend=alt.Legend(orient="bottom-right", offset=6),
        ),
        tooltip=[
            alt.Tooltip(LOCATION.translate(ESCAPE), title=LOCATION),
            alt.Tooltip(MAGNITUDE.translate(ESCAPE), title=MAGNITUDE, format=".1f"),
            alt.Tooltip(REGION.translate(ESCAPE), title=REGION),
            alt.Tooltip(LATITUDE.translate(ESCAPE), title=LATITUDE, format=".2f"),
            alt.Tooltip(LONGITUDE.translate(ESCAPE), title=LONGITUDE, format=".2f"),
        ],
    )
    .project(**PROJECTION)
)

chart = (
    (base_map + bubbles)
    .properties(
        title=alt.Title(text=TITLE, fontSize=15, anchor="middle", color=INK),
        width=VIEW_W,
        height=VIEW_H,
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_title(color=INK)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        titleColor=INK,
        labelColor=INK_SOFT,
        titleFontSize=11,
        labelFontSize=10,
        padding=6,
        cornerRadius=4,
    )
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad (never crop) to the canonical 3200 x 1800 canvas
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
w, h = img.size
if w > TW or h > TH:
    raise SystemExit(f"altair produced {w}x{h}, exceeds target {TW}x{TH}; shrink width/height")
if (w, h) != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - w) // 2, (TH - h) // 2))
    canvas.save(f"plot-{THEME}.png")
