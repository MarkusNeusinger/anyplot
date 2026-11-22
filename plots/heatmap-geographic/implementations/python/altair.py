"""anyplot.ai
heatmap-geographic: Geographic Heatmap for Spatial Density
Library: altair 6.1.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-19
"""

import os

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
LAND_FILL = "#E4E2D8" if THEME == "light" else "#2E2E29"
LAND_STROKE = "#9A988E" if THEME == "light" else "#5E5E56"

# Imprint palette (single-polarity continuous ramp uses positions 1 and 3)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [IMPRINT_PALETTE[0], IMPRINT_PALETTE[2]]

# Constants
BANDWIDTH_DEG = 0.9  # Gaussian kernel width in degrees: keeps city clusters apart without one blob per point
CELL_DEG = 0.25  # edge of one heatmap cell in degrees
MIN_SHARE = 0.03  # cells below this share of the peak density stay uncolored so the basemap shows through

# Columns: set these to your table's column names
LATITUDE = "Latitude"  # role: latitude
LONGITUDE = "Longitude"  # role: longitude
VALUE = "Activity weight"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("events.csv")
np.random.seed(42)
cities = [
    # (name, lat, lon, spread, n_points, weight_base)
    ("London", 51.5, -0.1, 0.8, 80, 1.5),
    ("Paris", 48.9, 2.3, 0.6, 70, 1.4),
    ("Berlin", 52.5, 13.4, 0.7, 55, 1.2),
    ("Madrid", 40.4, -3.7, 0.5, 50, 1.1),
    ("Rome", 41.9, 12.5, 0.4, 45, 1.0),
    ("Vienna", 48.2, 16.4, 0.4, 35, 0.9),
    ("Amsterdam", 52.4, 4.9, 0.3, 40, 1.0),
    ("Brussels", 50.8, 4.4, 0.3, 35, 0.9),
    ("Warsaw", 52.2, 21.0, 0.5, 40, 0.8),
    ("Prague", 50.1, 14.4, 0.3, 30, 0.8),
    ("Stockholm", 59.3, 18.1, 0.4, 30, 0.7),
    ("Munich", 48.1, 11.6, 0.3, 35, 0.9),
    ("Milan", 45.5, 9.2, 0.4, 40, 1.0),
    ("Barcelona", 41.4, 2.2, 0.4, 45, 1.0),
    ("Lisbon", 38.7, -9.1, 0.4, 30, 0.8),
]
frames = []
for _name, lat, lon, spread, n, weight in cities:
    frames.append(
        pd.DataFrame(
            {
                LATITUDE: np.random.normal(lat, spread, n),
                LONGITUDE: np.random.normal(lon, spread * 1.2, n),
                VALUE: np.random.exponential(weight, n) * 10,
            }
        )
    )
n_rural = 200
frames.append(
    pd.DataFrame(
        {
            LATITUDE: np.random.uniform(36, 62, n_rural),
            LONGITUDE: np.random.uniform(-10, 25, n_rural),
            VALUE: np.random.exponential(0.3, n_rural) * 5,
        }
    )
)
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
DENSITY = "Relative density (% of peak)"

# Weighted Gaussian kernel density on a regular lon/lat grid (separable kernels)
pad = 3 * BANDWIDTH_DEG
lon_edges = np.arange(df[LONGITUDE].min() - pad, df[LONGITUDE].max() + pad, CELL_DEG)
lat_edges = np.arange(df[LATITUDE].min() - pad, df[LATITUDE].max() + pad, CELL_DEG)
lon_mid = lon_edges + CELL_DEG / 2
lat_mid = lat_edges + CELL_DEG / 2
weights = df[VALUE].fillna(0).to_numpy()
kernel_lon = np.exp(-0.5 * ((lon_mid[:, None] - df[LONGITUDE].to_numpy()[None, :]) / BANDWIDTH_DEG) ** 2)
kernel_lat = np.exp(-0.5 * ((lat_mid[:, None] - df[LATITUDE].to_numpy()[None, :]) / BANDWIDTH_DEG) ** 2)
density = (kernel_lat * weights[None, :]) @ kernel_lon.T
density = 100 * density / density.max()

cells = pd.DataFrame(
    {
        "lon0": np.tile(lon_edges, len(lat_edges)),
        "lon1": np.tile(lon_edges + CELL_DEG, len(lat_edges)),
        "lat0": np.repeat(lat_edges, len(lon_edges)),
        "lat1": np.repeat(lat_edges + CELL_DEG, len(lon_edges)),
        DENSITY: density.ravel(),
    }
)
cells = cells[cells[DENSITY] >= MIN_SHARE * 100].round(3)

# Map view: centered on the data, scaled to fill the canvas
center = [float(df[LONGITUDE].median()), float(df[LATITUDE].median())]
PROJECTION = {"type": "mercator", "scale": 560, "center": center}

countries = alt.topo_feature("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json", "countries")
basemap = alt.Chart(countries).mark_geoshape(fill=LAND_FILL, stroke=LAND_STROKE, strokeWidth=0.4).project(**PROJECTION)

heat = (
    alt.Chart(cells)
    .mark_rect(stroke=None)
    .encode(
        longitude="lon0:Q",
        latitude="lat0:Q",
        longitude2="lon1:Q",
        latitude2="lat1:Q",
        color=alt.Color(
            DENSITY.translate(ESCAPE),
            type="quantitative",
            title=DENSITY,
            scale=alt.Scale(range=IMPRINT_SEQ, domain=[0, 100]),
            legend=alt.Legend(orient="right", gradientLength=140, gradientThickness=12, format=".0f"),
        ),
        opacity=alt.Opacity(
            DENSITY.translate(ESCAPE),
            type="quantitative",
            scale=alt.Scale(range=[0.3, 0.95], domain=[0, 100]),
            legend=None,
        ),
    )
    .project(**PROJECTION)
)

title = "European Activity Density · heatmap-geographic · python · altair · anyplot.ai"
chart = (
    alt.layer(basemap, heat)
    .properties(
        background=PAGE_BG, width=610, height=415, title=alt.Title(title, fontSize=14, anchor="middle", color=INK)
    )
    .configure_view(fill=PAGE_BG, strokeWidth=0)
    .configure_legend(
        fillColor=ELEVATED_BG,
        strokeColor=INK_SOFT,
        titleColor=INK,
        labelColor=INK_SOFT,
        titleFontSize=10,
        labelFontSize=9,
        padding=6,
        cornerRadius=3,
    )
)

# Save outputs, padding (never cropping) to the 3200 x 1800 target
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")
TW, TH = 3200, 1800
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.width > TW or img.height > TH:
    raise SystemExit(f"altair rendered {img.width}x{img.height}, exceeds {TW}x{TH}; shrink width/height")
if img.size != (TW, TH):
    canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    canvas.paste(img, ((TW - img.width) // 2, (TH - img.height) // 2))
    canvas.save(f"plot-{THEME}.png")
