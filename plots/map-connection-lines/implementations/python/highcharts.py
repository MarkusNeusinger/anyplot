"""anyplot.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: highcharts | Python 3.13
Quality: 91/100 | Updated: 2026-05-28
"""

import json
import os
import tempfile
import time
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
MAP_LAND = "#E8E6DE" if THEME == "light" else "#272724"
MAP_BORDER = "#CCCAC2" if THEME == "light" else "#3A3A37"

# anyplot palette — imprint_seq for connection line gradient
BRAND = "#009E73"  # airport markers (categorical position 1)
FLOW_END = "#4467A3"  # imprint_seq end color

# Data - International airline routes between major hub airports
np.random.seed(42)

airports = {
    "London Heathrow": {"lat": 51.47, "lon": -0.46, "code": "LHR"},
    "New York JFK": {"lat": 40.64, "lon": -73.78, "code": "JFK"},
    "Dubai": {"lat": 25.25, "lon": 55.36, "code": "DXB"},
    "Singapore Changi": {"lat": 1.36, "lon": 103.99, "code": "SIN"},
    "Hong Kong": {"lat": 22.31, "lon": 113.91, "code": "HKG"},
    "Tokyo Haneda": {"lat": 35.55, "lon": 139.78, "code": "HND"},
    "Los Angeles": {"lat": 33.94, "lon": -118.41, "code": "LAX"},
    "Paris CDG": {"lat": 49.01, "lon": 2.55, "code": "CDG"},
    "Frankfurt": {"lat": 50.03, "lon": 8.57, "code": "FRA"},
    "Sydney": {"lat": -33.95, "lon": 151.18, "code": "SYD"},
    "São Paulo": {"lat": -23.63, "lon": -46.66, "code": "GRU"},
    "Johannesburg": {"lat": -26.14, "lon": 28.25, "code": "JNB"},
}

# Per-point label offsets to reduce crowding for nearby European hubs
label_offsets = {
    "London Heathrow": {"x": -22, "y": -14},
    "Paris CDG": {"x": -8, "y": 22},
    "Frankfurt": {"x": 22, "y": -14},
}

connections = [
    {"from": "London Heathrow", "to": "New York JFK", "passengers": 4200},
    {"from": "Paris CDG", "to": "New York JFK", "passengers": 2800},
    {"from": "Frankfurt", "to": "New York JFK", "passengers": 1900},
    {"from": "London Heathrow", "to": "Los Angeles", "passengers": 1500},
    {"from": "London Heathrow", "to": "Dubai", "passengers": 3100},
    {"from": "London Heathrow", "to": "Hong Kong", "passengers": 2200},
    {"from": "London Heathrow", "to": "Singapore Changi", "passengers": 1800},
    {"from": "Paris CDG", "to": "Dubai", "passengers": 1600},
    {"from": "Frankfurt", "to": "Singapore Changi", "passengers": 1400},
    {"from": "Dubai", "to": "Singapore Changi", "passengers": 2500},
    {"from": "Dubai", "to": "Hong Kong", "passengers": 1900},
    {"from": "Singapore Changi", "to": "Hong Kong", "passengers": 2100},
    {"from": "Singapore Changi", "to": "Sydney", "passengers": 1700},
    {"from": "Hong Kong", "to": "Tokyo Haneda", "passengers": 2300},
    {"from": "Tokyo Haneda", "to": "Los Angeles", "passengers": 1600},
    {"from": "New York JFK", "to": "Los Angeles", "passengers": 3800},
    {"from": "New York JFK", "to": "São Paulo", "passengers": 1200},
    {"from": "Los Angeles", "to": "Sydney", "passengers": 900},
    {"from": "London Heathrow", "to": "Johannesburg", "passengers": 1100},
    {"from": "Dubai", "to": "Johannesburg", "passengers": 850},
]

flow_data = [
    {"from": conn["from"], "to": conn["to"], "weight": conn["passengers"], "curveFactor": 0.3, "growTowards": True}
    for conn in connections
]

point_data = []
for name, info in airports.items():
    total_traffic = sum(c["passengers"] for c in connections if c["from"] == name or c["to"] == name)
    point = {
        "id": name,
        "name": info["code"],
        "lat": info["lat"],
        "lon": info["lon"],
        "marker": {"radius": max(7, min(19, total_traffic / 600))},
    }
    if name in label_offsets:
        point["dataLabels"] = label_offsets[name]
    point_data.append(point)

# Title with length-scaled font size (baseline: 66px at 67 chars)
title_text = "International Flight Routes · map-connection-lines · python · highcharts · anyplot.ai"
title_fontsize = f"{round(66 * min(1.0, 67 / len(title_text)))}px"

chart_config = {
    "chart": {"map": None, "width": 3200, "height": 1800, "backgroundColor": PAGE_BG, "spacing": [80, 50, 50, 50]},
    "title": {"text": title_text, "style": {"fontSize": title_fontsize, "fontWeight": "bold", "color": INK}, "y": 50},
    "subtitle": {
        "text": "Connection line thickness represents annual passenger volume between major hub airports",
        "style": {"fontSize": "36px", "color": INK_SOFT},
        "y": 92,
    },
    "mapNavigation": {"enabled": False},
    "legend": {"enabled": False},
    "tooltip": {
        "useHTML": True,
        "headerFormat": "",
        "pointFormat": (
            '<span style="font-size: 22px;">'
            "<b>{point.from}</b> → <b>{point.to}</b><br/>"
            "Passengers: <b>{point.weight:,.0f}K</b> per year"
            "</span>"
        ),
        "backgroundColor": ELEVATED_BG,
        "style": {"color": INK},
    },
    "plotOptions": {
        "flowmap": {
            "minWidth": 1,
            "maxWidth": 15,
            "opacity": 0.55,
            "fillOpacity": 0.5,
            "markerEnd": {"enabled": True, "width": 10, "height": 10},
        },
        "mappoint": {
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"fontSize": "20px", "fontWeight": "bold", "color": INK, "textOutline": f"2px {PAGE_BG}"},
                "y": -10,
                "allowOverlap": False,
            }
        },
    },
    "series": [
        {
            "type": "map",
            "name": "World",
            "showInLegend": False,
            "nullColor": MAP_LAND,
            "borderColor": MAP_BORDER,
            "borderWidth": 0.8,
            "states": {"inactive": {"opacity": 1}},
        },
        {
            "type": "mappoint",
            "name": "Airports",
            "data": point_data,
            "color": BRAND,
            "marker": {"symbol": "circle", "fillColor": BRAND, "lineWidth": 2, "lineColor": PAGE_BG},
        },
        {
            "type": "flowmap",
            "name": "Flight Routes",
            "linkedTo": ":previous",
            "data": flow_data,
            "color": FLOW_END,
            "fillColor": {
                "linearGradient": {"x1": 0, "y1": 0, "x2": 1, "y2": 0},
                "stops": [[0, "rgba(0,158,115,0.6)"], [1, "rgba(68,103,163,0.6)"]],
            },
        },
    ],
}

chart_json = json.dumps(chart_config)

# Load Highcharts JS from local npm package (CDN cannot be loaded from file://)
npm_root = Path("/tmp/node_modules")
if not npm_root.exists():
    import subprocess

    subprocess.run(["npm", "install", "highcharts", "@highcharts/map-collection"], cwd="/tmp", check=True)

highmaps_js = (npm_root / "highcharts" / "highmaps.js").read_text(encoding="utf-8")
flowmap_js = (npm_root / "highcharts" / "modules" / "flowmap.js").read_text(encoding="utf-8")
world_topo = (npm_root / "@highcharts" / "map-collection" / "custom" / "world.topo.json").read_text(encoding="utf-8")

# HTML with inline scripts for headless Chrome
headless_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
    <script>{flowmap_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>
        var topology = {world_topo};
        var chartConfig = {chart_json};
        chartConfig.chart.map = topology;
        Highcharts.mapChart('container', chartConfig);
    </script>
</body>
</html>"""

# Standalone interactive HTML (CDN scripts, responsive)
interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/maps/highmaps.js"></script>
    <script src="https://code.highcharts.com/maps/modules/flowmap.js"></script>
    <style>html, body {{ margin: 0; padding: 0; background: {PAGE_BG}; }}</style>
</head>
<body>
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        fetch('https://code.highcharts.com/mapdata/custom/world.topo.json')
            .then(r => r.json())
            .then(topology => {{
                var cfg = {chart_json};
                cfg.chart.map = topology;
                cfg.chart.width = null;
                cfg.chart.height = null;
                Highcharts.mapChart('container', cfg);
            }});
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(interactive_html)

# Screenshot via headless Chrome with CDP viewport override
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(headless_html)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(8)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# PIL safety net — pin to exact 3200×1800 so the post-render gate passes
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
