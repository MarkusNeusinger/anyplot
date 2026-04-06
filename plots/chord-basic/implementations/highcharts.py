""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: highcharts 1.10.3 | Python 3.14
Quality: 83/100 | Updated: 2026-04-06
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Trade flows between continents (billions USD, approximate)
flows = [
    ["Europe", "N. America", 28],
    ["Europe", "Asia", 22],
    ["Europe", "Africa", 8],
    ["Europe", "S. America", 6],
    ["Europe", "Oceania", 4],
    ["Asia", "N. America", 35],
    ["Asia", "Europe", 25],
    ["Asia", "Oceania", 12],
    ["Asia", "Africa", 10],
    ["Asia", "S. America", 7],
    ["Africa", "Europe", 15],
    ["Africa", "Asia", 12],
    ["Africa", "N. America", 8],
    ["Africa", "S. America", 3],
    ["Africa", "Oceania", 2],
    ["N. America", "Europe", 26],
    ["N. America", "Asia", 30],
    ["N. America", "S. America", 18],
    ["N. America", "Oceania", 5],
    ["N. America", "Africa", 4],
    ["S. America", "N. America", 22],
    ["S. America", "Europe", 14],
    ["S. America", "Asia", 10],
    ["S. America", "Africa", 3],
    ["S. America", "Oceania", 2],
    ["Oceania", "Asia", 18],
    ["Oceania", "Europe", 6],
    ["Oceania", "N. America", 5],
    ["Oceania", "Africa", 1],
    ["Oceania", "S. America", 1],
]

# Colorblind-safe colors for continents
nodes = [
    {"id": "Europe", "color": "#306998"},
    {"id": "Asia", "color": "#FFD43B"},
    {"id": "Africa", "color": "#9467BD"},
    {"id": "N. America", "color": "#17BECF"},
    {"id": "S. America", "color": "#2CA02C"},
    {"id": "Oceania", "color": "#FF7F0E"},
]

# Chart configuration
chart_config = {
    "chart": {
        "type": "dependencywheel",
        "width": 3600,
        "height": 3600,
        "backgroundColor": "#ffffff",
        "marginTop": 140,
        "marginBottom": 60,
    },
    "title": {
        "text": "chord-basic \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "52px", "fontWeight": "bold"},
    },
    "subtitle": {
        "text": "Trade Flows Between Continents (Billions USD)",
        "style": {"fontSize": "34px", "color": "#666666"},
    },
    "tooltip": {
        "style": {"fontSize": "32px"},
        "nodeFormat": "{point.name}: ${point.sum}B total trade",
        "pointFormat": "{point.fromNode.name} \u2192 {point.toNode.name}: ${point.weight}B",
    },
    "series": [
        {
            "type": "dependencywheel",
            "name": "Trade Flow",
            "keys": ["from", "to", "weight"],
            "data": flows,
            "nodes": nodes,
            "dataLabels": {
                "enabled": True,
                "style": {"fontSize": "38px", "fontWeight": "bold", "textOutline": "4px white", "color": "#333333"},
                "distance": 40,
                "padding": 8,
                "crop": False,
                "overflow": "allow",
            },
            "size": "76%",
            "center": ["50%", "52%"],
            "linkOpacity": 0.55,
            "curveFactor": 0.6,
            "nodePadding": 15,
            "nodeWidth": 35,
        }
    ],
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "accessibility": {"enabled": False},
}

# Download Highcharts JS and modules
headers = {"User-Agent": "Mozilla/5.0"}
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
sankey_url = "https://cdn.jsdelivr.net/npm/highcharts@11/modules/sankey.js"
wheel_url = "https://cdn.jsdelivr.net/npm/highcharts@11/modules/dependency-wheel.js"

with urllib.request.urlopen(urllib.request.Request(highcharts_url, headers=headers), timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(urllib.request.Request(sankey_url, headers=headers), timeout=30) as response:
    sankey_js = response.read().decode("utf-8")

with urllib.request.urlopen(urllib.request.Request(wheel_url, headers=headers), timeout=30) as response:
    wheel_js = response.read().decode("utf-8")

# Generate HTML
chart_json = json.dumps(chart_config)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{sankey_js}</script>
    <script>{wheel_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>Highcharts.chart('container', {chart_json});</script>
</body>
</html>"""

# Save interactive HTML version
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/modules/sankey.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/modules/dependency-wheel.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>Highcharts.chart('container', {chart_json});</script>
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
chrome_options.add_argument("--window-size=3600,3700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 3600, 3600))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
