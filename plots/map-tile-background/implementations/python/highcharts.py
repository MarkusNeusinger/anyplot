""" anyplot.ai
map-tile-background: Map with Tile Background
Library: highcharts unknown | Python 3.13.13
Quality: 87/100 | Created: 2026-05-27
"""

import json
import math
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Tile provider — switch here to try alternatives:
#   {"type": "OpenStreetMap"}                — standard street map (default)
#   {"type": "Stamen", "theme": "Terrain"}   — terrain shading with labels
#   {"type": "Stamen", "theme": "Toner"}     — high-contrast black & white
#   {"type": "USGS", "theme": "USTopo"}      — USGS topographic map
#   {"type": "USGS", "theme": "USImagery"}   — satellite imagery
TILE_PROVIDER = {"type": "OpenStreetMap"}
TILE_CREDIT = "Tiles © OpenStreetMap contributors"

# Data: major European cities — annual international visitor counts (millions, ~2023)
cities = [
    {"name": "Paris", "lat": 48.8566, "lon": 2.3522, "visitors": 38.5},
    {"name": "London", "lat": 51.5074, "lon": -0.1278, "visitors": 31.2},
    {"name": "Rome", "lat": 41.9028, "lon": 12.4964, "visitors": 22.0},
    {"name": "Madrid", "lat": 40.4168, "lon": -3.7038, "visitors": 13.9},
    {"name": "Berlin", "lat": 52.5200, "lon": 13.4050, "visitors": 13.1},
    {"name": "Barcelona", "lat": 41.3851, "lon": 2.1734, "visitors": 12.1},
    {"name": "Amsterdam", "lat": 52.3676, "lon": 4.9041, "visitors": 10.5},
    {"name": "Vienna", "lat": 48.2082, "lon": 16.3738, "visitors": 8.7},
    {"name": "Prague", "lat": 50.0755, "lon": 14.4378, "visitors": 7.9},
    {"name": "Budapest", "lat": 47.4979, "lon": 19.0402, "visitors": 5.8},
    {"name": "Lisbon", "lat": 38.7169, "lon": -9.1399, "visitors": 5.4},
    {"name": "Athens", "lat": 37.9838, "lon": 23.7275, "visitors": 5.2},
    {"name": "Copenhagen", "lat": 55.6761, "lon": 12.5683, "visitors": 4.9},
    {"name": "Stockholm", "lat": 59.3293, "lon": 18.0686, "visitors": 4.5},
    {"name": "Warsaw", "lat": 52.2297, "lon": 21.0122, "visitors": 3.8},
]

# Derive map center and zoom from data bounds so the view adapts if data changes
lats = [c["lat"] for c in cities]
lons = [c["lon"] for c in cities]
map_center = [(min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2]  # [lon, lat]
lon_span = (max(lons) - min(lons)) * 1.25  # 25% padding each side
map_zoom = round(math.log2(360 / lon_span * (3200 / 256)) - 1, 1)
map_zoom = max(3.0, min(8.0, map_zoom))

max_visitors = max(c["visitors"] for c in cities)
mappoint_data = [
    {
        "name": c["name"],
        "lat": c["lat"],
        "lon": c["lon"],
        "visitors": c["visitors"],
        "marker": {"radius": int(round(8 + (c["visitors"] / max_visitors) * 22))},
    }
    for c in cities
]

title = "European Tourism · map-tile-background · python · highcharts · anyplot.ai"
title_fontsize = round(66 * min(1.0, 67 / len(title)))

chart_config = {
    "chart": {
        "type": "map",
        "width": 3200,
        "height": 1800,
        "backgroundColor": PAGE_BG,
        "margin": [120, 40, 60, 40],
        "style": {"fontFamily": "'Helvetica Neue', Arial, sans-serif"},
    },
    "title": {
        "text": title,
        "style": {"fontSize": f"{title_fontsize}px", "color": INK, "fontWeight": "500"},
        "margin": 8,
    },
    "subtitle": {
        "text": "Annual international arrivals — bubble size proportional to visitor volume",
        "style": {"fontSize": "34px", "color": INK_SOFT},
        "margin": 18,
    },
    "credits": {"text": TILE_CREDIT, "style": {"color": INK_SOFT, "fontSize": "22px"}},
    "legend": {"enabled": False},
    "mapNavigation": {"enabled": True, "enableButtons": True},
    "mapView": {"center": map_center, "zoom": map_zoom},
    "series": [
        {"type": "tiledwebmap", "provider": TILE_PROVIDER, "showInLegend": False},
        {
            "type": "mappoint",
            "name": "Cities",
            "color": ANYPLOT_PALETTE[0],
            "data": mappoint_data,
            "cursor": "pointer",
            "marker": {"symbol": "circle", "lineColor": PAGE_BG, "lineWidth": 2, "fillOpacity": 0.85},
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"color": INK, "fontSize": "34px", "fontWeight": "400", "textOutline": f"3px {PAGE_BG}"},
                "y": -18,
                "padding": 0,
            },
            "tooltip": {"headerFormat": "", "pointFormat": "<b>{point.name}</b><br>Visitors: {point.visitors}M/yr"},
        },
    ],
}

# Download Highcharts Maps JS files (inline for headless Chrome file:// loading)
highmaps_js = None
for url in ["https://code.highcharts.com/maps/highmaps.js", "https://cdn.jsdelivr.net/npm/highcharts/highmaps.js"]:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            highmaps_js = resp.read().decode("utf-8")
        break
    except Exception:
        continue
if highmaps_js is None:
    raise RuntimeError("Could not download highmaps.js from any CDN")

tiledwebmap_js = None
for url in [
    "https://code.highcharts.com/maps/modules/tiledwebmap.js",
    "https://cdn.jsdelivr.net/npm/highcharts/modules/tiledwebmap.js",
]:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            tiledwebmap_js = resp.read().decode("utf-8")
        break
    except Exception:
        continue
if tiledwebmap_js is None:
    raise RuntimeError("Could not download tiledwebmap.js from any CDN")

chart_json = json.dumps(chart_config)

# Dark mode: invert OSM tiles via CSS filter applied to SVG image elements after tiles load.
# This is the standard browser dark-map technique: invert(1) hue-rotate(200deg) turns
# white land → dark gray and blue water → dark teal, matching the dark page surface.
dark_filter_script = (
    """
    setTimeout(function() {
        document.querySelectorAll('#container image').forEach(function(img) {
            img.style.filter = 'invert(1) hue-rotate(200deg) brightness(0.75) saturate(0.85)';
        });
    }, 5000);
    """
    if THEME == "dark"
    else ""
)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
    <script>{tiledwebmap_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG}; overflow:hidden;">
    <div id="container" style="width:3200px; height:1800px;"></div>
    <script>
    Highcharts.mapChart('container', {chart_json});
    {dark_filter_script}
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--allow-running-insecure-content")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(12)  # allow tiles and dark filter setTimeout(5s) to complete
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Normalize to exact canvas dimensions
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
