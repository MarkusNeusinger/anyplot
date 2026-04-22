""" pyplots.ai
flowmap-origin-destination: Origin-Destination Flow Map
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - International trade flows between major ports (synthetic but realistic)
np.random.seed(42)

# Major trading ports with coordinates
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

# Trade flows with volumes (in arbitrary units for visualization)
flows = [
    # Asia to Americas
    {"from": "Shanghai", "to": "Los Angeles", "volume": 450},
    {"from": "Shanghai", "to": "New York", "volume": 280},
    {"from": "Hong Kong", "to": "Los Angeles", "volume": 320},
    {"from": "Busan", "to": "Los Angeles", "volume": 180},
    {"from": "Tokyo", "to": "Los Angeles", "volume": 150},
    # Asia to Europe
    {"from": "Shanghai", "to": "Rotterdam", "volume": 380},
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

# Prepare flow data for Highcharts flowmap
flow_data = []
for flow in flows:
    origin = ports[flow["from"]]
    dest = ports[flow["to"]]
    flow_data.append(
        {
            "from": flow["from"],
            "to": flow["to"],
            "weight": flow["volume"],
            "curveFactor": 0.25,  # Bezier curve factor for arc shape
            "growTowards": True,
        }
    )

# Prepare point data for markers
point_data = []
for name, coords in ports.items():
    # Calculate total flow for marker size
    total_flow = sum(f["volume"] for f in flows if f["from"] == name or f["to"] == name)
    point_data.append(
        {
            "id": name,
            "name": name,
            "lat": coords["lat"],
            "lon": coords["lon"],
            "marker": {
                "radius": max(8, min(25, total_flow / 50))  # Size based on traffic
            },
        }
    )

# Chart configuration
chart_config = {
    "chart": {
        "map": None,  # Will be set by topology
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "spacing": [120, 80, 80, 80],
    },
    "title": {
        "text": "Global Maritime Trade Routes \u00b7 flowmap-origin-destination \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "56px", "fontWeight": "bold"},
        "y": 70,
    },
    "subtitle": {
        "text": "Arc thickness proportional to shipping volume between major ports",
        "style": {"fontSize": "40px", "color": "#666666"},
        "y": 120,
    },
    "mapNavigation": {"enabled": False},
    "legend": {
        "enabled": False  # Flow maps don't need traditional legend
    },
    "tooltip": {
        "useHTML": True,
        "headerFormat": "",
        "pointFormat": '<span style="font-size: 28px;">'
        "<b>{point.from}</b> \u2192 <b>{point.to}</b><br/>"
        "Volume: <b>{point.weight}</b> units"
        "</span>",
    },
    "plotOptions": {
        "flowmap": {
            "minWidth": 2,
            "maxWidth": 25,
            "opacity": 0.6,
            "fillOpacity": 0.5,
            "markerEnd": {"enabled": True, "width": 15, "height": 15},
        },
        "mappoint": {
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"fontSize": "24px", "fontWeight": "bold", "textOutline": "3px white"},
                "y": -15,
            }
        },
    },
    "series": [
        {
            "type": "map",
            "name": "World",
            "showInLegend": False,
            "nullColor": "#e8e8e8",
            "borderColor": "#aaaaaa",
            "borderWidth": 1,
            "states": {"inactive": {"opacity": 1}},
        },
        {
            "type": "mappoint",
            "name": "Ports",
            "data": point_data,
            "color": "#306998",
            "marker": {"symbol": "circle", "fillColor": "#306998", "lineWidth": 3, "lineColor": "#ffffff"},
        },
        {
            "type": "flowmap",
            "name": "Trade Routes",
            "linkedTo": ":previous",
            "data": flow_data,
            "color": "#FFD43B",
            "fillColor": {
                "linearGradient": {"x1": 0, "y1": 0, "x2": 1, "y2": 0},
                "stops": [
                    [0, "rgba(48, 105, 152, 0.7)"],  # Python Blue
                    [1, "rgba(255, 212, 59, 0.7)"],  # Python Yellow
                ],
            },
        },
    ],
}

# Convert to JSON for JavaScript
chart_json = json.dumps(chart_config)

# Download required JavaScript files
highmaps_url = "https://code.highcharts.com/maps/highmaps.js"
flowmap_url = "https://code.highcharts.com/maps/modules/flowmap.js"
world_url = "https://code.highcharts.com/mapdata/custom/world.topo.json"

with urllib.request.urlopen(highmaps_url, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(flowmap_url, timeout=60) as response:
    flowmap_js = response.read().decode("utf-8")

with urllib.request.urlopen(world_url, timeout=60) as response:
    world_topo = response.read().decode("utf-8")

# Generate HTML with inline scripts for headless rendering
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
    <script>{flowmap_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var topology = {world_topo};
        var chartConfig = {chart_json};
        chartConfig.chart.map = topology;
        Highcharts.mapChart('container', chartConfig);
    </script>
</body>
</html>"""

# Save HTML for interactive version
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/maps/highmaps.js"></script>
    <script src="https://code.highcharts.com/maps/modules/flowmap.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        fetch('https://code.highcharts.com/mapdata/custom/world.topo.json')
            .then(response => response.json())
            .then(topology => {{
                var chartConfig = {chart_json};
                chartConfig.chart.map = topology;
                Highcharts.mapChart('container', chartConfig);
            }});
    </script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(8)  # Wait longer for flowmap to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
