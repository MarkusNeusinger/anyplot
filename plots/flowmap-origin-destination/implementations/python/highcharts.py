""" anyplot.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-20
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1
MAP_FILL = "#E0DDD4" if THEME == "light" else "#2E2E2A"
MAP_BORDER = "#B8B5AA" if THEME == "light" else "#5A5A50"

# Data - International maritime trade flows between major ports
ports = {
    "Shanghai": {"lat": 31.2, "lon": 121.5},
    "Singapore": {"lat": 1.3, "lon": 103.8},
    "Rotterdam": {"lat": 51.9, "lon": 4.5},
    "Los Angeles": {"lat": 33.7, "lon": -118.3},
    "Dubai": {"lat": 25.3, "lon": 55.3},
    "Hong Kong": {"lat": 22.3, "lon": 114.2},
    "Busan": {"lat": 35.1, "lon": 129.0},
    "Hamburg": {"lat": 53.5, "lon": 9.9},
    "New York": {"lat": 40.7, "lon": -74.0},
    "Tokyo": {"lat": 35.5, "lon": 139.8},
    "Sydney": {"lat": -33.9, "lon": 151.2},
    "Santos": {"lat": -23.9, "lon": -46.3},
}

flows = [
    # Asia to Americas (trans-Pacific, bidirectional on top routes)
    {"from": "Shanghai", "to": "Los Angeles", "volume": 450},
    {"from": "Los Angeles", "to": "Shanghai", "volume": 220},
    {"from": "Shanghai", "to": "New York", "volume": 280},
    {"from": "Hong Kong", "to": "Los Angeles", "volume": 320},
    {"from": "Busan", "to": "Los Angeles", "volume": 180},
    {"from": "Tokyo", "to": "Los Angeles", "volume": 150},
    # Asia to Europe (trans-Suez, bidirectional on top routes)
    {"from": "Shanghai", "to": "Rotterdam", "volume": 380},
    {"from": "Rotterdam", "to": "Shanghai", "volume": 140},
    {"from": "Shanghai", "to": "Hamburg", "volume": 220},
    {"from": "Singapore", "to": "Rotterdam", "volume": 290},
    {"from": "Hong Kong", "to": "Rotterdam", "volume": 200},
    # Asia internal
    {"from": "Shanghai", "to": "Singapore", "volume": 350},
    {"from": "Busan", "to": "Shanghai", "volume": 260},
    {"from": "Tokyo", "to": "Hong Kong", "volume": 180},
    # Middle East hub
    {"from": "Shanghai", "to": "Dubai", "volume": 280},
    {"from": "Singapore", "to": "Dubai", "volume": 220},
    {"from": "Dubai", "to": "Rotterdam", "volume": 310},
    # Americas to Europe
    {"from": "New York", "to": "Rotterdam", "volume": 190},
    {"from": "Santos", "to": "Rotterdam", "volume": 160},
    # Oceania connections
    {"from": "Sydney", "to": "Shanghai", "volume": 140},
    {"from": "Sydney", "to": "Singapore", "volume": 120},
]

flow_data = []
for flow in flows:
    flow_data.append(
        {"from": flow["from"], "to": flow["to"], "weight": flow["volume"], "curveFactor": 0.25, "growTowards": True}
    )

label_offsets = {"Busan": {"y": -30}, "Hong Kong": {"y": 10}}

point_data = []
for name, coords in ports.items():
    total_flow = sum(f["volume"] for f in flows if f["from"] == name or f["to"] == name)
    point = {
        "id": name,
        "name": name,
        "lat": coords["lat"],
        "lon": coords["lon"],
        "marker": {"radius": max(8, min(22, total_flow / 60))},
    }
    if name in label_offsets:
        point["dataLabels"] = {"y": label_offsets[name]["y"]}
    point_data.append(point)

chart_config = {
    "chart": {"map": None, "width": 3200, "height": 1800, "backgroundColor": PAGE_BG, "spacing": [80, 60, 80, 60]},
    "title": {
        "text": "flowmap-origin-destination · python · highcharts · anyplot.ai",
        "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK},
        "y": 50,
    },
    "subtitle": {
        "text": "Global maritime trade routes — arc width ∝ shipping volume, arrows show flow direction",
        "style": {"fontSize": "40px", "color": INK_SOFT},
        "y": 110,
    },
    "mapNavigation": {"enabled": False},
    "legend": {
        "enabled": True,
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
        "itemStyle": {"color": INK_SOFT, "fontSize": "44px"},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
    },
    "tooltip": {
        "useHTML": True,
        "headerFormat": "",
        "pointFormat": (
            '<span style="font-size: 30px;">'
            "<b>{point.from}</b> → <b>{point.to}</b><br/>"
            "Volume: <b>{point.weight}</b> units"
            "</span>"
        ),
    },
    "plotOptions": {
        "flowmap": {
            "minWidth": 2,
            "maxWidth": 22,
            "opacity": 0.70,
            "fillOpacity": 0.65,
            "markerEnd": {"enabled": True, "width": 12, "height": 12},
        },
        "mappoint": {
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"fontSize": "44px", "fontWeight": "bold", "textOutline": f"3px {PAGE_BG}", "color": INK},
                "y": -18,
            }
        },
    },
    "series": [
        {
            "type": "map",
            "name": "World",
            "showInLegend": False,
            "nullColor": MAP_FILL,
            "borderColor": MAP_BORDER,
            "borderWidth": 0.5,
            "states": {"inactive": {"opacity": 1}},
        },
        {
            "type": "mappoint",
            "name": "Ports",
            "data": point_data,
            "showInLegend": True,
            "color": BRAND,
            "marker": {"symbol": "circle", "fillColor": BRAND, "lineWidth": 2, "lineColor": PAGE_BG},
        },
        {
            "type": "flowmap",
            "name": "Trade Routes",
            "linkedTo": ":previous",
            "data": flow_data,
            "showInLegend": True,
            "color": BRAND,
            "fillColor": {
                "linearGradient": {"x1": 0, "y1": 0, "x2": 1, "y2": 0},
                "stops": [[0, "rgba(0, 158, 115, 0.60)"], [1, "rgba(68, 103, 163, 0.60)"]],
            },
        },
    ],
}

chart_json = json.dumps(chart_config)

# Download required JavaScript and map topology
highmaps_url = "https://unpkg.com/highcharts/highmaps.js"
flowmap_url = "https://unpkg.com/highcharts/modules/flowmap.js"
world_url = "https://unpkg.com/@highcharts/map-collection/custom/world.topo.json"

with urllib.request.urlopen(highmaps_url, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(flowmap_url, timeout=60) as response:
    flowmap_js = response.read().decode("utf-8")

with urllib.request.urlopen(world_url, timeout=60) as response:
    world_topo = response.read().decode("utf-8")

# HTML with inline scripts for headless Chrome screenshot
html_content = f"""<!DOCTYPE html>
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

# Save interactive HTML artifact (CDN-based for portability)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://unpkg.com/highcharts/highmaps.js"></script>
    <script src="https://unpkg.com/highcharts/modules/flowmap.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        fetch('https://unpkg.com/@highcharts/map-collection/custom/world.topo.json')
            .then(response => response.json())
            .then(topology => {{
                var chartConfig = {chart_json};
                chartConfig.chart.map = topology;
                chartConfig.chart.width = null;
                chartConfig.chart.height = null;
                Highcharts.mapChart('container', chartConfig);
            }});
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Screenshot via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(8)  # Wait for flowmap module to fully render
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
