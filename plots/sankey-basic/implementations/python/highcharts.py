""" anyplot.ai
sankey-basic: Basic Sankey Diagram
Library: highcharts unknown | Python 3.13.13
Quality: 85/100 | Updated: 2026-04-30
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data - U.S. Energy flow from sources to sectors (values in TWh)
flows = [
    ["Coal", "Electricity", 150],
    ["Coal", "Industrial", 80],
    ["Natural Gas", "Electricity", 120],
    ["Natural Gas", "Residential", 90],
    ["Natural Gas", "Commercial", 60],
    ["Natural Gas", "Industrial", 50],
    ["Nuclear", "Electricity", 200],
    ["Petroleum", "Transportation", 280],
    ["Petroleum", "Industrial", 70],
    ["Petroleum", "Residential", 30],
    ["Renewable", "Electricity", 100],
    ["Renewable", "Transportation", 20],
    ["Electricity", "Residential", 180],
    ["Electricity", "Commercial", 160],
    ["Electricity", "Industrial", 140],
]

# Node colors - dark tones ensuring white text readability on all nodes
node_colors = {
    "Coal": "#1A3A5C",
    "Natural Gas": "#6B4E12",
    "Nuclear": "#5B2E8F",
    "Petroleum": "#0A6B78",
    "Renewable": "#155415",
    "Electricity": "#4D2A22",
    "Residential": "#8B3A6B",
    "Commercial": "#3A3A3A",
    "Industrial": "#5B5C0A",
    "Transportation": "#994D00",
}

nodes_set = set()
for source, target, _ in flows:
    nodes_set.add(source)
    nodes_set.add(target)

nodes_data = [{"id": node, "name": node, "color": node_colors.get(node, "#306998")} for node in nodes_set]
links_data = [{"from": source, "to": target, "weight": value} for source, target, value in flows]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "sankey",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginLeft": 180,
    "marginRight": 180,
    "marginTop": 160,
    "marginBottom": 80,
}

chart.options.title = {
    "text": "sankey-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {"text": "U.S. Energy Flow (values in TWh)", "style": {"fontSize": "40px", "color": INK_SOFT}}

chart.options.tooltip = {
    "style": {"fontSize": "36px"},
    "nodeFormat": "{point.name}: {point.sum} TWh",
    "pointFormat": "{point.fromNode.name} → {point.toNode.name}: {point.weight} TWh",
}

chart.options.series = [
    {
        "type": "sankey",
        "name": "Energy Flow",
        "keys": ["from", "to", "weight"],
        "nodes": nodes_data,
        "data": links_data,
        "dataLabels": {
            "enabled": True,
            "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#FFFFFF", "textOutline": "3px #333333"},
            "nodeFormat": "{point.name}",
        },
        "nodeWidth": 50,
        "nodePadding": 35,
        "linkOpacity": 0.5,
        "curveFactor": 0.5,
        "colorByPoint": True,
        "linkColorMode": "from",
    }
]

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

# Download Highcharts JS and sankey module inline (required for headless Chrome)
with urllib.request.urlopen("https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js", timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen("https://cdn.jsdelivr.net/npm/highcharts@latest/modules/sankey.js", timeout=30) as response:
    sankey_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{sankey_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome
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
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
