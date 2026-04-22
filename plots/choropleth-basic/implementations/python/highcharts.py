""" pyplots.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Population density by European country (synthetic data)
np.random.seed(42)
countries = [
    ("de", "Germany", 234),
    ("fr", "France", 119),
    ("gb", "United Kingdom", 275),
    ("it", "Italy", 206),
    ("es", "Spain", 94),
    ("pl", "Poland", 124),
    ("nl", "Netherlands", 508),
    ("be", "Belgium", 376),
    ("se", "Sweden", 25),
    ("at", "Austria", 107),
    ("ch", "Switzerland", 215),
    ("pt", "Portugal", 112),
    ("cz", "Czech Republic", 137),
    ("dk", "Denmark", 137),
    ("no", "Norway", 15),
    ("ie", "Ireland", 72),
    ("fi", "Finland", 18),
    ("gr", "Greece", 82),
    ("hu", "Hungary", 107),
    ("ro", "Romania", 84),
]

# Format data for Highcharts map series
map_data = [{"code": code.upper(), "name": name, "value": value} for code, name, value in countries]

# Create JavaScript configuration for Highmaps
chart_config = {
    "chart": {
        "map": None,  # Will be set by topology
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "spacing": [80, 100, 80, 80],
    },
    "title": {
        "text": "choropleth-basic \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "72px", "fontWeight": "bold"},
        "y": 50,
    },
    "subtitle": {
        "text": "Population Density (people per km\u00b2)",
        "style": {"fontSize": "48px", "color": "#666666"},
        "y": 110,
    },
    "mapNavigation": {"enabled": False},
    "colorAxis": {
        "min": 0,
        "max": 550,
        "stops": [
            [0, "#f7fbff"],
            [0.2, "#c6dbef"],
            [0.4, "#6baed6"],
            [0.6, "#306998"],
            [0.8, "#2171b5"],
            [1, "#08306b"],
        ],
        "labels": {"style": {"fontSize": "36px"}},
    },
    "legend": {
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
        "floating": False,
        "backgroundColor": "rgba(255, 255, 255, 0.95)",
        "padding": 30,
        "symbolHeight": 700,
        "symbolWidth": 50,
        "itemStyle": {"fontSize": "36px"},
        "title": {"text": "Density<br/>(per km\u00b2)", "style": {"fontSize": "40px", "fontWeight": "bold"}},
    },
    "tooltip": {
        "style": {"fontSize": "36px"},
        "headerFormat": "",
        "pointFormat": "<b>{point.name}</b><br/>Density: {point.value} per km\u00b2",
    },
    "series": [
        {
            "type": "map",
            "name": "Population Density",
            "data": map_data,
            "joinBy": ["iso-a2", "code"],
            "states": {"hover": {"color": "#FFD43B"}},
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"fontSize": "24px", "fontWeight": "normal", "textOutline": "3px white"},
            },
            "borderColor": "#ffffff",
            "borderWidth": 3,
            "nullColor": "#e0e0e0",
        }
    ],
}

# Convert to JSON for JavaScript
chart_json = json.dumps(chart_config)

# Download required JavaScript files
highcharts_url = "https://code.highcharts.com/maps/highmaps.js"
europe_url = "https://code.highcharts.com/mapdata/custom/europe.topo.json"

with urllib.request.urlopen(highcharts_url, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

with urllib.request.urlopen(europe_url, timeout=60) as response:
    europe_topo = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        var topology = {europe_topo};
        var chartConfig = {chart_json};
        chartConfig.chart.map = topology;
        Highcharts.mapChart('container', chartConfig);
    </script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/maps/highmaps.js"></script>
    <script src="https://code.highcharts.com/mapdata/custom/europe.topo.json"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        fetch('https://code.highcharts.com/mapdata/custom/europe.topo.json')
            .then(response => response.json())
            .then(topology => {{
                var chartConfig = {chart_json};
                chartConfig.chart.map = topology;
                Highcharts.mapChart('container', chartConfig);
            }});
    </script>
</body>
</html>"""
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
time.sleep(6)  # Wait for chart to render (maps need more time)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
