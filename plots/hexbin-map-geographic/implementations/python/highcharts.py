"""anyplot.ai
hexbin-map-geographic: Hexagonal Binning Map
Library: highcharts unknown | Python 3.13.13
Quality: 84/100 | Created: 2026-05-27
"""

import json
import math
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Continuous colormap: imprint_seq (brand green → blue)
CMAP_START = "#009E73"
CMAP_END = "#4467A3"

# Data: wildlife sightings in Yellowstone / Grand Teton region (synthetic)
np.random.seed(42)

observation_zones = [
    {"lat": 44.42, "lon": -110.59, "n": 1500, "s": 0.15},
    {"lat": 44.68, "lon": -110.84, "n": 900, "s": 0.10},
    {"lat": 44.89, "lon": -110.40, "n": 700, "s": 0.12},
    {"lat": 43.87, "lon": -110.73, "n": 1000, "s": 0.13},
    {"lat": 44.15, "lon": -110.20, "n": 600, "s": 0.10},
    {"lat": 44.52, "lon": -111.08, "n": 500, "s": 0.09},
    {"lat": 44.25, "lon": -109.85, "n": 700, "s": 0.12},
]

all_lats, all_lons = [], []
for zone in observation_zones:
    lat_pts = np.random.normal(zone["lat"], zone["s"], zone["n"])
    lon_pts = np.random.normal(zone["lon"], zone["s"], zone["n"])
    all_lats.extend(lat_pts.tolist())
    all_lons.extend(lon_pts.tolist())

lats = np.array(all_lats)
lons = np.array(all_lons)

LAT_MIN, LAT_MAX = 43.4, 45.4
LON_MIN, LON_MAX = -111.6, -109.4
mask = (lats >= LAT_MIN) & (lats <= LAT_MAX) & (lons >= LON_MIN) & (lons <= LON_MAX)
lats = lats[mask]
lons = lons[mask]

# Hexagonal binning: offset coordinate system (pointy-top hexagons)
HEX_R = 0.11
COL_SPACING = HEX_R * math.sqrt(3)
ROW_SPACING = HEX_R * 1.5

bins = {}
for lat, lon in zip(lats.tolist(), lons.tolist(), strict=False):
    col = round((lon - LON_MIN) / COL_SPACING)
    if col % 2 == 0:
        row = round((lat - LAT_MIN) / ROW_SPACING)
    else:
        row = round((lat - LAT_MIN - ROW_SPACING / 2) / ROW_SPACING)
    key = (col, row)
    bins[key] = bins.get(key, 0) + 1

tilemap_data = sorted(
    [{"x": col, "y": row, "value": count} for (col, row), count in bins.items()], key=lambda d: (d["x"], d["y"])
)

# Geographic context: state borders converted to tilemap grid coordinates
# Grid x = (lon - LON_MIN) / COL_SPACING, grid y = (lat - LAT_MIN) / ROW_SPACING
GRID_X_MAX = (LON_MAX - LON_MIN) / COL_SPACING
GRID_Y_MAX = (LAT_MAX - LAT_MIN) / ROW_SPACING
MT_WY_BORDER_Y = (45.0 - LAT_MIN) / ROW_SPACING  # Montana–Wyoming: 45°N
ID_WY_BORDER_X = (-111.054 - LON_MIN) / COL_SPACING  # Idaho–Wyoming: ~111.054°W

# Subtle state-region fill colors (drawn under hexagons as base map layer)
BAND_WY = "rgba(0,158,115,0.08)"  # brand green tint — Wyoming
BAND_MT = "rgba(68,103,163,0.08)"  # brand blue tint — Montana
BAND_ID = "rgba(44,188,205,0.08)"  # brand cyan tint — Idaho

# Title
TITLE = "Yellowstone Sightings · hexbin-map-geographic · python · highcharts · anyplot.ai"
TITLE_FONTSIZE = round(66 * min(1.0, 67 / len(TITLE)))

# Download Highcharts JS + tilemap module (CDN requires browser headers)
_hdrs = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"}

_req = urllib.request.Request("https://code.highcharts.com/maps/highmaps.js", headers=_hdrs)
with urllib.request.urlopen(_req, timeout=60) as resp:
    highmaps_js = resp.read().decode("utf-8")

_req2 = urllib.request.Request("https://code.highcharts.com/maps/modules/tilemap.js", headers=_hdrs)
with urllib.request.urlopen(_req2, timeout=60) as resp:
    tilemap_js = resp.read().decode("utf-8")

chart_options = {
    "chart": {
        "width": 3200,
        "height": 1800,
        "backgroundColor": PAGE_BG,
        "style": {"fontFamily": "Arial, sans-serif", "color": INK},
        "marginTop": 120,
        "marginBottom": 190,
        "marginLeft": 210,
        "marginRight": 230,
        "plotBorderWidth": 0,
    },
    "title": {
        "text": TITLE,
        "style": {"fontSize": f"{TITLE_FONTSIZE}px", "color": INK, "fontWeight": "500"},
        "margin": 20,
    },
    "subtitle": {
        "text": "Wildlife observations aggregated into ~12 km hexagonal cells · Yellowstone–Grand Teton region",
        "style": {"fontSize": "38px", "color": INK_SOFT},
        "margin": 18,
    },
    "xAxis": {
        "title": {"text": "Longitude (°W)", "style": {"fontSize": "56px", "color": INK}, "margin": 14},
        "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "tickLength": 0,
        "gridLineColor": GRID,
        "gridLineWidth": 1,
        # Base map: Idaho region west of the WY border
        "plotBands": [
            {
                "from": 0,
                "to": ID_WY_BORDER_X,
                "color": BAND_ID,
                "zIndex": 0,
                "label": {
                    "text": "Idaho",
                    "style": {"fontSize": "34px", "color": INK_SOFT, "fontStyle": "italic"},
                    "align": "center",
                    "y": 30,
                },
            }
        ],
        # Dashed state border line (ID | WY)
        "plotLines": [
            {
                "value": ID_WY_BORDER_X,
                "color": INK_SOFT,
                "width": 2,
                "dashStyle": "ShortDash",
                "zIndex": 3,
                "label": {
                    "text": "ID | WY",
                    "style": {"fontSize": "30px", "color": INK_SOFT},
                    "align": "center",
                    "y": -12,
                },
            }
        ],
    },
    "yAxis": {
        "title": {"text": "Latitude (°N)", "style": {"fontSize": "56px", "color": INK}, "margin": 14},
        "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "tickLength": 0,
        "gridLineColor": GRID,
        "gridLineWidth": 1,
        # Base map: Wyoming (south) and Montana (north) state regions
        "plotBands": [
            {
                "from": 0,
                "to": MT_WY_BORDER_Y,
                "color": BAND_WY,
                "zIndex": 0,
                "label": {
                    "text": "Wyoming",
                    "style": {"fontSize": "34px", "color": INK_SOFT, "fontStyle": "italic"},
                    "align": "right",
                    "x": -8,
                    "y": 20,
                },
            },
            {
                "from": MT_WY_BORDER_Y,
                "to": GRID_Y_MAX + 0.5,
                "color": BAND_MT,
                "zIndex": 0,
                "label": {
                    "text": "Montana",
                    "style": {"fontSize": "34px", "color": INK_SOFT, "fontStyle": "italic"},
                    "align": "right",
                    "x": -8,
                    "y": 20,
                },
            },
        ],
        # Dashed state border line (MT | WY)
        "plotLines": [
            {
                "value": MT_WY_BORDER_Y,
                "color": INK_SOFT,
                "width": 2,
                "dashStyle": "ShortDash",
                "zIndex": 3,
                "label": {
                    "text": "MT | WY border · 45°N",
                    "style": {"fontSize": "30px", "color": INK_SOFT},
                    "align": "right",
                    "x": -6,
                    "y": -6,
                },
            }
        ],
    },
    "colorAxis": {
        "minColor": CMAP_START,
        "maxColor": CMAP_END,
        "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
        "title": {"text": "Sightings per cell", "style": {"fontSize": "44px", "color": INK_SOFT}},
    },
    "legend": {
        "enabled": True,
        "itemStyle": {"color": INK_SOFT, "fontSize": "44px"},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
    },
    "tooltip": {"backgroundColor": ELEVATED_BG, "borderColor": INK_SOFT, "style": {"color": INK, "fontSize": "40px"}},
    "plotOptions": {
        "tilemap": {
            "tileShape": "hexagon",
            "borderColor": PAGE_BG,
            "borderWidth": 1.5,
            "opacity": 0.90,
            "turboThreshold": 10000,
        }
    },
    "series": [{"type": "tilemap", "name": "Wildlife Sightings", "data": tilemap_data}],
    "credits": {"enabled": False},
}

chart_options_json = json.dumps(chart_options)

# Geographic coordinate converters embedded in JS formatter strings
x_formatter_js = (
    f"function() {{"
    f"var lon = {LON_MIN:.4f} + this.value * {COL_SPACING:.6f};"
    f"return Math.abs(lon).toFixed(1) + '\\u00b0W';"
    f"}}"
)

y_formatter_js = (
    f"function() {{var lat = {LAT_MIN:.4f} + this.value * {ROW_SPACING:.6f};return lat.toFixed(1) + '\\u00b0N';}}"
)

tooltip_js = (
    f"function() {{"
    f"var lon = ({LON_MIN:.4f} + this.point.x * {COL_SPACING:.6f}).toFixed(2);"
    f"var lat = ({LAT_MIN:.4f} + this.point.y * {ROW_SPACING:.6f}).toFixed(2);"
    f"return '<b>Wildlife Sightings</b><br>'"
    f"+ '~' + Math.abs(lon) + '\\u00b0W, ' + lat + '\\u00b0N<br>'"
    f"+ '<b>Count: ' + this.point.value + '</b>';"
    f"}}"
)

chart_init_js = f"""
var opts = {chart_options_json};
opts.xAxis.labels.formatter = {x_formatter_js};
opts.yAxis.labels.formatter = {y_formatter_js};
opts.tooltip.formatter = {tooltip_js};
Highcharts.chart('container', opts);
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
    <script>{tilemap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:3200px; height:1800px;"></div>
    <script>{chart_init_js}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as fh:
    fh.write(html_content)

# Screenshot via Selenium / headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as fh:
    fh.write(html_content)
    tmp_path = fh.name

chrome_opts = Options()
chrome_opts.add_argument("--headless=new")
chrome_opts.add_argument("--no-sandbox")
chrome_opts.add_argument("--disable-dev-shm-usage")
chrome_opts.add_argument("--disable-gpu")
chrome_opts.add_argument("--hide-scrollbars")
chrome_opts.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_opts)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{tmp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
Path(tmp_path).unlink()

# Pin to exact 3200×1800 (belt-and-braces against ±1–2 px rounding)
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _canvas = Image.new("RGB", (3200, 1800), PAGE_BG)
    _canvas.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _canvas.save(f"plot-{THEME}.png")
