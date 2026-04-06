""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: highcharts 1.10.3 | Python 3.14
Quality: 89/100 | Updated: 2026-04-06
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.dependencywheel import DependencyWheelSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Trade flows between continents (billions USD, approximate)
flows = [
    {"from": "Europe", "to": "N. America", "weight": 28},
    {"from": "Europe", "to": "Asia", "weight": 22},
    {"from": "Europe", "to": "Africa", "weight": 8},
    {"from": "Europe", "to": "S. America", "weight": 6},
    {"from": "Europe", "to": "Oceania", "weight": 4},
    {"from": "Asia", "to": "N. America", "weight": 35},
    {"from": "Asia", "to": "Europe", "weight": 25},
    {"from": "Asia", "to": "Oceania", "weight": 12},
    {"from": "Asia", "to": "Africa", "weight": 10},
    {"from": "Asia", "to": "S. America", "weight": 7},
    {"from": "Africa", "to": "Europe", "weight": 15},
    {"from": "Africa", "to": "Asia", "weight": 12},
    {"from": "Africa", "to": "N. America", "weight": 8},
    {"from": "Africa", "to": "S. America", "weight": 3},
    {"from": "Africa", "to": "Oceania", "weight": 2},
    {"from": "N. America", "to": "Europe", "weight": 26},
    {"from": "N. America", "to": "Asia", "weight": 30},
    {"from": "N. America", "to": "S. America", "weight": 18},
    {"from": "N. America", "to": "Oceania", "weight": 5},
    {"from": "N. America", "to": "Africa", "weight": 4},
    {"from": "S. America", "to": "N. America", "weight": 22},
    {"from": "S. America", "to": "Europe", "weight": 14},
    {"from": "S. America", "to": "Asia", "weight": 10},
    {"from": "S. America", "to": "Africa", "weight": 3},
    {"from": "S. America", "to": "Oceania", "weight": 2},
    {"from": "Oceania", "to": "Asia", "weight": 18},
    {"from": "Oceania", "to": "Europe", "weight": 6},
    {"from": "Oceania", "to": "N. America", "weight": 5},
    {"from": "Oceania", "to": "Africa", "weight": 1},
    {"from": "Oceania", "to": "S. America", "weight": 1},
]

# Refined palette — harmonious, colorblind-safe, muted-professional tones
node_defs = [
    {"id": "Europe", "color": "#306998"},
    {"id": "Asia", "color": "#E8A838"},
    {"id": "Africa", "color": "#8B6CAF"},
    {"id": "N. America", "color": "#2BA5B5"},
    {"id": "S. America", "color": "#3DAA6D"},
    {"id": "Oceania", "color": "#D4654A"},
]

# Build chart using highcharts-core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3600,
    "height": 3600,
    "backgroundColor": {
        "linearGradient": {"x1": 0, "y1": 0, "x2": 0.3, "y2": 1},
        "stops": [[0, "#FAFBFC"], [0.5, "#F4F6F9"], [1, "#EEF1F5"]],
    },
    "marginTop": 150,
    "marginBottom": 30,
    "marginLeft": 30,
    "marginRight": 30,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
}

chart.options.title = {
    "text": "chord-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "60px", "fontWeight": "700", "color": "#1A2332", "letterSpacing": "0.5px"},
    "y": 45,
}

chart.options.subtitle = {
    "text": "Trade Flows Between Continents (Billions USD)",
    "style": {"fontSize": "40px", "fontWeight": "400", "color": "#5A6878", "letterSpacing": "0.3px"},
    "y": 105,
}

chart.options.tooltip = {
    "style": {"fontSize": "32px"},
    "backgroundColor": "rgba(255,255,255,0.96)",
    "borderWidth": 1,
    "borderColor": "#DDE1E6",
    "shadow": {"color": "rgba(0,0,0,0.08)", "offsetX": 2, "offsetY": 2, "width": 6},
    "nodeFormat": "<b>{point.name}</b><br/>Total: ${point.sum}B",
    "pointFormat": "{point.fromNode.name} \u2192 {point.toNode.name}<br/><b>${point.weight}B</b>",
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.accessibility = {"enabled": False}

# Build series using Python API
series = DependencyWheelSeries()
series.data = flows
series.nodes = node_defs
series.name = "Trade Flow"
series.data_labels = {
    "enabled": True,
    "style": {"fontSize": "44px", "fontWeight": "600", "textOutline": "5px rgba(255,255,255,0.92)", "color": "#1A2332"},
    "distance": 40,
    "padding": 10,
    "crop": False,
    "overflow": "allow",
}
series.size = "84%"
series.center = ["50%", "53%"]
series.link_opacity = 0.5
series.curve_factor = 0.6
series.node_padding = 16
series.node_width = 44
series.border_width = 2
series.border_color = "rgba(255,255,255,0.75)"
series.color_by_point = True
series.min_link_width = 4

chart.add_series(series)

# Generate JS literal for embedding
chart_js = chart.to_js_literal()

# Download Highcharts JS and modules
headers = {"User-Agent": "Mozilla/5.0"}
urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/modules/sankey.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/modules/dependency-wheel.js",
]
scripts = []
for url in urls:
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        scripts.append(response.read().decode("utf-8"))

highcharts_js, sankey_js, wheel_js = scripts

# Generate HTML with inline scripts for headless Chrome
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body {{ margin: 0; font-family: 'Inter', 'Segoe UI', sans-serif; }}
        #container {{ width: 3600px; height: 3600px; }}
    </style>
    <script>{highcharts_js}</script>
    <script>{sankey_js}</script>
    <script>{wheel_js}</script>
</head>
<body>
    <div id="container"></div>
    <script>
        Highcharts.setOptions({{
            chart: {{ style: {{ fontFamily: "'Inter', 'Segoe UI', Helvetica, sans-serif" }} }}
        }});
        {chart_js}
    </script>
</body>
</html>"""

# Save interactive HTML version (CDN-based for portability)
standalone_js = chart_js.replace(
    "document.addEventListener('DOMContentLoaded', function() {",
    "document.addEventListener('DOMContentLoaded', function() {",
)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body {{ margin: 0; font-family: 'Inter', 'Segoe UI', sans-serif; }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/modules/sankey.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/modules/dependency-wheel.js"></script>
</head>
<body>
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        Highcharts.setOptions({{
            chart: {{ style: {{ fontFamily: "'Inter', 'Segoe UI', Helvetica, sans-serif" }} }}
        }});
        {standalone_js}
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
