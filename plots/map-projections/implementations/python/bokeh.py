"""anyplot.ai
map-projections: World Map with Different Projections
Library: bokeh 3.10.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import json
import os
import sys
import time
import urllib.request
from pathlib import Path


# Prevent this file (bokeh.py) from shadowing the installed bokeh package
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir in sys.path:
    sys.path.remove(_this_dir)

import numpy as np
from bokeh.io import output_file, save
from bokeh.layouts import column, gridplot
from bokeh.models import DataRange1d, Div, FixedTicker, Legend, LegendItem
from bokeh.plotting import figure
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1: the Tissot indicatrices

# --- Natural Earth 110m country outlines (outer rings of every polygon) ---
NE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
)
ne_cache = Path(__file__).parent / "countries_110m.json"
if not ne_cache.exists():
    with urllib.request.urlopen(NE_URL, timeout=30) as response:
        ne_cache.write_bytes(response.read())
with ne_cache.open() as f:
    world = json.load(f)

land_rings = []
for feature in world["features"]:
    geometry = feature["geometry"]
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    land_rings.extend(np.array(polygon[0], dtype=float) for polygon in polygons)

# Layers shared by all four panels; only the projection differs
GRATICULE_STEP = 30  # degrees between graticule lines
TISSOT_RADIUS = 8  # angular radius of each indicatrix, degrees on the sphere
TISSOT_LATS = [-60, -30, 0, 30, 60]
TISSOT_LONS = [-150, -90, -30, 30, 90, 150]
LAT_LABELS = [-60, -30, 0, 30, 60]
LON_LABELS = [-120, -60, 0, 60, 120]
PROJECTIONS = [
    ("Equirectangular (Plate Carrée)", "equirectangular", 89.0, "Tissot circle (stretches east-west)"),
    ("Mercator", "mercator", 75.0, "Tissot circle (stays round, grows poleward)"),
    ("Sinusoidal", "sinusoidal", 89.0, "Tissot circle (equal-area, shears)"),
    ("Mollweide", "mollweide", 89.0, "Tissot circle (equal-area, squeezed)"),
]

# Each layer is an array of vertices: shape id, longitude, latitude
land = np.vstack([np.column_stack([np.full(len(ring), i), ring[:, :2]]) for i, ring in enumerate(land_rings)])
layers = [("land", land)]

grat = []
shape = 0
for lon in range(-180, 181, GRATICULE_STEP):
    lat = np.linspace(-90, 90, 120)
    grat.append(np.column_stack([np.full(120, shape), np.full(120, lon), lat]))
    shape += 1
for lat in range(-60, 61, GRATICULE_STEP):
    lon = np.linspace(-180, 180, 240)
    grat.append(np.column_stack([np.full(240, shape), lon, np.full(240, lat)]))
    shape += 1
layers.append(("graticule", np.vstack(grat)))

# Geodesic circles of constant angular radius on the sphere
tissot = []
bearing = np.linspace(0, 2 * np.pi, 60)
r = np.radians(TISSOT_RADIUS)
shape = 0
for lat0 in TISSOT_LATS:
    for lon0 in TISSOT_LONS:
        phi0 = np.radians(lat0)
        phi = np.arcsin(np.sin(phi0) * np.cos(r) + np.cos(phi0) * np.sin(r) * np.cos(bearing))
        lam = np.radians(lon0) + np.arctan2(
            np.sin(bearing) * np.sin(r) * np.cos(phi0), np.cos(r) - np.sin(phi0) * np.sin(phi)
        )
        tissot.append(np.column_stack([np.full(60, shape), np.degrees(lam), np.degrees(phi)]))
        shape += 1
layers.append(("tissot", np.vstack(tissot)))

# Plot
PANEL_W, PANEL_H = 1600, 805
panels = []


def project(kind, lat_clip, lon_deg, lat_deg):
    """Project degrees to map units; latitude is clipped where the projection blows up."""
    lam = np.radians(lon_deg)
    phi = np.radians(np.clip(lat_deg, -lat_clip, lat_clip))
    if kind == "mercator":
        return lam, np.log(np.tan(np.pi / 4 + phi / 2))
    if kind == "sinusoidal":
        return lam * np.cos(phi), phi
    if kind == "mollweide":
        theta = phi.copy()  # Newton iteration for the auxiliary angle
        for _ in range(40):
            theta -= (2 * theta + np.sin(2 * theta) - np.pi * np.sin(phi)) / (2 + 2 * np.cos(2 * theta) + 1e-12)
        return (2 * np.sqrt(2) / np.pi) * lam * np.cos(theta), np.sqrt(2) * np.sin(theta)
    return lam, phi


for title, kind, lat_clip, tissot_label in PROJECTIONS:
    p = figure(
        width=PANEL_W,
        height=PANEL_H,
        title=title,
        toolbar_location=None,
        x_range=DataRange1d(range_padding=0.01),
        y_range=DataRange1d(range_padding=0.01),
        match_aspect=True,
        min_border_left=150,
        min_border_right=30,
        min_border_top=20,
        min_border_bottom=10,
    )
    p.background_fill_color = PAGE_BG
    p.border_fill_color = PAGE_BG
    p.outline_line_color = INK_SOFT
    p.outline_line_width = 1
    p.title.text_color = INK
    p.title.text_font_size = "32pt"
    p.title.text_font_style = "bold"
    p.title.align = "center"
    p.xgrid.visible = False
    p.ygrid.visible = False

    xs, ys = {}, {}
    for layer, data in layers:
        x, y = project(kind, lat_clip, data[:, 1], data[:, 2])
        shape_ids = data[:, 0]
        parts_x, parts_y = [], []
        for s in np.unique(shape_ids):
            mask = shape_ids == s
            parts_x.append(x[mask].tolist())
            parts_y.append(y[mask].tolist())
        xs[layer], ys[layer] = parts_x, parts_y

    p.patches(
        xs=xs["land"],
        ys=ys["land"],
        fill_color=INK_SOFT,
        fill_alpha=0.15,
        line_color=INK_SOFT,
        line_width=1,
        line_alpha=0.6,
    )
    graticule = p.multi_line(xs=xs["graticule"], ys=ys["graticule"], line_color=INK_SOFT, line_width=3, line_alpha=0.8)
    rings = p.multi_line(xs=xs["tissot"], ys=ys["tissot"], line_color=BRAND, line_width=5, line_alpha=0.95)

    # Latitude labels on the left axis, longitude labels along the equator below the map
    lat_x, lat_y = project(kind, lat_clip, np.zeros(len(LAT_LABELS)), np.array(LAT_LABELS, dtype=float))
    lon_x, _ = project(kind, lat_clip, np.array(LON_LABELS, dtype=float), np.zeros(len(LON_LABELS)))
    p.yaxis.ticker = FixedTicker(ticks=lat_y.tolist())
    p.yaxis.major_label_overrides = {
        float(v): f"{abs(d)}°{'N' if d > 0 else 'S' if d < 0 else ''}" for v, d in zip(lat_y, LAT_LABELS, strict=True)
    }
    p.xaxis.ticker = FixedTicker(ticks=lon_x.tolist())
    p.xaxis.major_label_overrides = {
        float(v): f"{abs(d)}°{'E' if d > 0 else 'W' if d < 0 else ''}" for v, d in zip(lon_x, LON_LABELS, strict=True)
    }
    for axis in (p.xaxis, p.yaxis):
        axis.major_label_text_font_size = "30pt"
        axis.major_label_text_color = INK_SOFT
        axis.axis_line_color = None
        axis.major_tick_line_color = None
        axis.minor_tick_line_color = None
        axis.major_label_standoff = 10

    legend = Legend(
        items=[
            LegendItem(label="Graticule (30° steps)", renderers=[graticule]),
            LegendItem(label=tissot_label, renderers=[rings]),
        ],
        orientation="horizontal",
        label_text_font_size="26pt",
        label_text_color=INK_SOFT,
        background_fill_color=ELEVATED_BG,
        border_line_color=INK_SOFT,
        glyph_width=80,
        glyph_height=40,
        label_standoff=16,
        spacing=30,
        padding=14,
    )
    p.add_layout(legend, "below")
    panels.append(p)

grid = gridplot([panels[:2], panels[2:]], merge_tools=False, toolbar_location=None)

title_div = Div(
    text=(
        f"<style>body,html{{background:{PAGE_BG};margin:0;padding:0;}}</style>"
        f"<div style='background:{PAGE_BG};text-align:center;padding:14px 0 0 0;width:3200px;"
        f"font-family:sans-serif;'>"
        f"<span style='font-size:40pt;font-weight:bold;color:{INK};'>"
        f"map-projections · python · bokeh · anyplot.ai</span><br>"
        f"<span style='font-size:26pt;color:{INK_SOFT};'>"
        f"Green Tissot indicatrices reveal distortion: size shows area error, "
        f"shape shows angular error.</span></div>"
    ),
    width=3200,
    height=130,
)

output_file(f"plot-{THEME}.html")
save(column(title_div, grid, spacing=0))

W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H + 200}",
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H + 200)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Pin the PNG to exactly 3200x1800
img = Image.open(f"plot-{THEME}.png")
if img.size != (W, H):
    canvas = Image.new("RGB", (W, H), PAGE_BG)
    canvas.paste(img.crop((0, 0, min(img.size[0], W), min(img.size[1], H))), (0, 0))
    canvas.save(f"plot-{THEME}.png")
