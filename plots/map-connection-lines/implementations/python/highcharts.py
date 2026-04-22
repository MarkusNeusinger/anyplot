""" pyplots.ai
map-connection-lines: Connection Lines Map (Origin-Destination)
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-21
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - International airline routes between major hub airports
np.random.seed(42)

# Major international airport hubs with coordinates
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

# Flight connections with passenger volumes (thousands per year, synthetic but realistic scale)
connections = [
    # Transatlantic routes
    {"from": "London Heathrow", "to": "New York JFK", "passengers": 4200},
    {"from": "Paris CDG", "to": "New York JFK", "passengers": 2800},
    {"from": "Frankfurt", "to": "New York JFK", "passengers": 1900},
    {"from": "London Heathrow", "to": "Los Angeles", "passengers": 1500},
    # Europe to Middle East/Asia
    {"from": "London Heathrow", "to": "Dubai", "passengers": 3100},
    {"from": "London Heathrow", "to": "Hong Kong", "passengers": 2200},
    {"from": "London Heathrow", "to": "Singapore Changi", "passengers": 1800},
    {"from": "Paris CDG", "to": "Dubai", "passengers": 1600},
    {"from": "Frankfurt", "to": "Singapore Changi", "passengers": 1400},
    # Asia-Pacific hub connections
    {"from": "Dubai", "to": "Singapore Changi", "passengers": 2500},
    {"from": "Dubai", "to": "Hong Kong", "passengers": 1900},
    {"from": "Singapore Changi", "to": "Hong Kong", "passengers": 2100},
    {"from": "Singapore Changi", "to": "Sydney", "passengers": 1700},
    {"from": "Hong Kong", "to": "Tokyo Haneda", "passengers": 2300},
    {"from": "Tokyo Haneda", "to": "Los Angeles", "passengers": 1600},
    # Americas connections
    {"from": "New York JFK", "to": "Los Angeles", "passengers": 3800},
    {"from": "New York JFK", "to": "São Paulo", "passengers": 1200},
    {"from": "Los Angeles", "to": "Sydney", "passengers": 900},
    # Africa connections
    {"from": "London Heathrow", "to": "Johannesburg", "passengers": 1100},
    {"from": "Dubai", "to": "Johannesburg", "passengers": 850},
]

# Prepare connection line data for Highcharts flowmap
flow_data = []
for conn in connections:
    flow_data.append(
        {
            "from": conn["from"],
            "to": conn["to"],
            "weight": conn["passengers"],
            "curveFactor": 0.3,  # Curve factor for great circle arc appearance
            "growTowards": True,
        }
    )

# Prepare airport marker data
point_data = []
for name, info in airports.items():
    # Calculate total passenger traffic for marker size
    total_traffic = sum(c["passengers"] for c in connections if c["from"] == name or c["to"] == name)
    point_data.append(
        {
            "id": name,
            "name": f"{info['code']}",
            "lat": info["lat"],
            "lon": info["lon"],
            "marker": {
                "radius": max(10, min(28, total_traffic / 400))  # Size based on traffic
            },
        }
    )

# Chart configuration
chart_config = {
    "chart": {
        "map": None,  # Will be set by world topology
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "spacing": [100, 60, 60, 60],
    },
    "title": {
        "text": "International Flight Routes · map-connection-lines · highcharts · pyplots.ai",
        "style": {"fontSize": "54px", "fontWeight": "bold"},
        "y": 60,
    },
    "subtitle": {
        "text": "Connection line thickness represents annual passenger volume between major hub airports",
        "style": {"fontSize": "36px", "color": "#666666"},
        "y": 110,
    },
    "mapNavigation": {"enabled": False},
    "legend": {"enabled": False},
    "tooltip": {
        "useHTML": True,
        "headerFormat": "",
        "pointFormat": '<span style="font-size: 28px;">'
        "<b>{point.from}</b> → <b>{point.to}</b><br/>"
        "Passengers: <b>{point.weight:,.0f}K</b> per year"
        "</span>",
    },
    "plotOptions": {
        "flowmap": {
            "minWidth": 2,
            "maxWidth": 22,
            "opacity": 0.5,
            "fillOpacity": 0.45,
            "markerEnd": {"enabled": True, "width": 12, "height": 12},
        },
        "mappoint": {
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"fontSize": "22px", "fontWeight": "bold", "textOutline": "3px white"},
                "y": -12,
            }
        },
    },
    "series": [
        {
            "type": "map",
            "name": "World",
            "showInLegend": False,
            "nullColor": "#f0f0f0",
            "borderColor": "#cccccc",
            "borderWidth": 1,
            "states": {"inactive": {"opacity": 1}},
        },
        {
            "type": "mappoint",
            "name": "Airports",
            "data": point_data,
            "color": "#306998",
            "marker": {"symbol": "circle", "fillColor": "#306998", "lineWidth": 3, "lineColor": "#ffffff"},
        },
        {
            "type": "flowmap",
            "name": "Flight Routes",
            "linkedTo": ":previous",
            "data": flow_data,
            "color": "#FFD43B",
            "fillColor": {
                "linearGradient": {"x1": 0, "y1": 0, "x2": 1, "y2": 0},
                "stops": [
                    [0, "rgba(48, 105, 152, 0.65)"],  # Python Blue
                    [1, "rgba(255, 212, 59, 0.65)"],  # Python Yellow
                ],
            },
        },
    ],
}

# Convert configuration to JSON
chart_json = json.dumps(chart_config)

# Download required JavaScript files for headless rendering
highmaps_url = "https://code.highcharts.com/maps/highmaps.js"
flowmap_url = "https://code.highcharts.com/maps/modules/flowmap.js"
world_url = "https://code.highcharts.com/mapdata/custom/world.topo.json"

with urllib.request.urlopen(highmaps_url, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(flowmap_url, timeout=60) as response:
    flowmap_js = response.read().decode("utf-8")

with urllib.request.urlopen(world_url, timeout=60) as response:
    world_topo = response.read().decode("utf-8")

# Generate HTML with inline scripts for headless Chrome
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

# Save standalone HTML for interactive viewing
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

# Write temp HTML and take screenshot using headless Chrome
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
time.sleep(8)  # Wait for flowmap to fully render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
