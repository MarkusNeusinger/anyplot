"""anyplot.ai
map-projections: World Map with Different Projections
Library: highcharts unknown | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-23
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# anyplot palette
LAND_COLOR = "#009E73"  # position 1 — brand green (land masses)
GRATICULE_COLOR = "#9418DB"  # position 2 — purple (lat/lon grid)

W, H = 3200, 1800

# Projections to compare
projections = [
    {
        "name": "Miller Cylindrical",
        "projection": {"name": "Miller"},
        "description": "Compromise cylindrical — moderate area distortion",
    },
    {
        "name": "Equal Earth",
        "projection": {"name": "EqualEarth"},
        "description": "Equal-area — preserves relative land sizes",
    },
    {
        "name": "Orthographic · Americas",
        "projection": {"name": "Orthographic", "rotation": [90, 0]},
        "description": "Globe view centered on the Americas",
    },
    {
        "name": "Robinson",
        "projection": {"name": "Robinson"},
        "description": "Compromise projection — balances shape and area",
    },
]

# Build Highcharts Maps configs
chart_configs = []
for proj in projections:
    config = {
        "chart": {
            "map": None,  # set dynamically in JS
            "backgroundColor": ELEVATED_BG,
            "spacing": [10, 10, 10, 10],
        },
        "title": {"text": proj["name"], "style": {"fontSize": "36px", "fontWeight": "bold", "color": INK}},
        "subtitle": {"text": proj["description"], "style": {"fontSize": "36px", "color": INK_SOFT}},
        "mapNavigation": {"enabled": False},
        "mapView": {"projection": proj["projection"]},
        "legend": {"enabled": False},
        "colorAxis": {"visible": False},
        "credits": {"enabled": False},
        "series": [
            {
                "type": "map",
                "name": "Countries",
                "showInLegend": False,
                "allAreas": True,
                "nullColor": LAND_COLOR,
                "borderColor": PAGE_BG,
                "borderWidth": 1.5,
                "states": {"hover": {"color": "#B71D27"}, "inactive": {"opacity": 1}},
            },
            {
                "type": "mapline",
                "name": "Graticule",
                "data": None,  # set dynamically in JS
                "color": GRATICULE_COLOR,
                "opacity": 0.45,
                "lineWidth": 1,
                "dashStyle": "ShortDash",
                "enableMouseTracking": False,
                "showInLegend": False,
            },
        ],
    }
    chart_configs.append(config)

# Generate graticule (lat/lon grid lines) as GeoJSON
graticule_features = []
for lon in range(-180, 181, 30):
    coords = [[lon, lat] for lat in range(-90, 91, 5)]
    label = f"{abs(lon)}°{'E' if lon > 0 else ('W' if lon < 0 else '')}"
    graticule_features.append(
        {"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords}, "properties": {"name": label}}
    )
for lat in range(-60, 61, 30):
    coords = [[lon, lat] for lon in range(-180, 181, 5)]
    label = f"{abs(lat)}°{'N' if lat > 0 else ('S' if lat < 0 else '')}"
    graticule_features.append(
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {"name": label if lat != 0 else "Eq"},
        }
    )

graticule_geojson = {"type": "FeatureCollection", "features": graticule_features}
graticule_json = json.dumps(graticule_geojson)

# Download Highmaps JS and world topology (embedded inline for headless Chrome)
# Use jsdelivr CDN — code.highcharts.com returns 403 in this environment
highmaps_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highmaps.js"
world_url = "https://cdn.jsdelivr.net/npm/@highcharts/map-collection/custom/world.topo.json"
proj_url = "https://cdn.jsdelivr.net/npm/proj4@2/dist/proj4.js"

with urllib.request.urlopen(highmaps_url, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(world_url, timeout=60) as response:
    world_topo = response.read().decode("utf-8")

try:
    with urllib.request.urlopen(proj_url, timeout=30) as response:
        proj4_js = response.read().decode("utf-8")
except Exception:
    proj4_js = ""

configs_json = [json.dumps(c) for c in chart_configs]

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
    {f"<script>{proj4_js}</script>" if proj4_js else ""}
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            width: {W}px;
            height: {H}px;
            overflow: hidden;
            background: {PAGE_BG};
            font-family: Arial, Helvetica, sans-serif;
            display: flex;
            flex-direction: column;
            padding: 28px 30px 20px 30px;
        }}
        h1 {{
            text-align: center;
            font-size: 60px;
            font-weight: bold;
            color: {INK};
            margin-bottom: 8px;
            flex-shrink: 0;
            line-height: 1.1;
        }}
        .subtitle {{
            text-align: center;
            font-size: 30px;
            color: {INK_SOFT};
            margin-bottom: 16px;
            flex-shrink: 0;
            line-height: 1.1;
        }}
        .grid {{
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 18px;
            overflow: hidden;
            min-height: 0;
        }}
        .chart-cell {{
            background: {ELEVATED_BG};
            border-radius: 6px;
            overflow: hidden;
            min-height: 0;
        }}
    </style>
</head>
<body>
    <h1>map-projections &middot; python &middot; highcharts &middot; anyplot.ai</h1>
    <div class="subtitle">Comparing cartographic projections: how each transforms Earth&#39;s sphere to a flat surface</div>
    <div class="grid">
        <div id="container0" class="chart-cell"></div>
        <div id="container1" class="chart-cell"></div>
        <div id="container2" class="chart-cell"></div>
        <div id="container3" class="chart-cell"></div>
    </div>
    <script>
        var topology = {world_topo};
        var graticule = {graticule_json};
        var graticuleData = Highcharts.geojson(graticule, 'mapline');
        var configs = [{configs_json[0]}, {configs_json[1]}, {configs_json[2]}, {configs_json[3]}];
        configs.forEach(function(config, i) {{
            config.chart.map = topology;
            config.chart.renderTo = 'container' + i;
            config.series[1].data = graticuleData;
            Highcharts.mapChart(config);
        }});
    </script>
</body>
</html>"""

# Save theme-suffixed HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via Selenium with exact viewport control
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument(f"--window-size={W},{H}")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone is eaten by Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(7)  # 4 map charts with projections need extra render time
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Belt-and-braces: pin to exact canvas dims in case of ±1–2 px rounding
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.size != (W, H):
    canvas = Image.new("RGB", (W, H), PAGE_BG)
    canvas.paste(img, ((W - img.size[0]) // 2, (H - img.size[1]) // 2))
    canvas.save(f"plot-{THEME}.png")
