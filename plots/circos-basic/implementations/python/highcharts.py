""" pyplots.ai
circos-basic: Circos Plot
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


# Data - Simulating trade flows between 8 regions
np.random.seed(42)

regions = ["N.America", "S.America", "Europe", "Africa", "MidEast", "S.Asia", "E.Asia", "Oceania"]

# Generate flow matrix - inter-regional trade flows
n_regions = len(regions)
flow_matrix = np.zeros((n_regions, n_regions))

# Create realistic flow patterns with some regions having stronger connections
for i in range(n_regions):
    for j in range(n_regions):
        if i != j:
            base_flow = np.random.exponential(50)
            # Some regional pairs have stronger trade relationships
            if (i == 0 and j == 6) or (i == 6 and j == 0):  # North America - East Asia
                base_flow *= 3
            elif (i == 2 and j == 6) or (i == 6 and j == 2):  # Europe - East Asia
                base_flow *= 2.5
            elif (i == 0 and j == 2) or (i == 2 and j == 0):  # North America - Europe
                base_flow *= 2
            flow_matrix[i, j] = base_flow

# Prepare data for Highcharts dependency wheel (circular chord-like visualization)
# Format: [from, to, weight] arrays
connections = []
for i in range(n_regions):
    for j in range(n_regions):
        if i != j and flow_matrix[i, j] > 20:  # Filter small connections
            connections.append([regions[i], regions[j], float(round(flow_matrix[i, j], 1))])

# Colorblind-safe colors for each region
colors = [
    "#306998",  # Python Blue - N. America
    "#FFD43B",  # Python Yellow - S. America
    "#9467BD",  # Purple - Europe
    "#17BECF",  # Cyan - Africa
    "#8C564B",  # Brown - Mid. East
    "#E377C2",  # Pink - S. Asia
    "#2CA02C",  # Green - E. Asia
    "#BCBD22",  # Olive - Oceania
]

# Full region names for legend
region_full_names = [
    "North America",
    "South America",
    "Europe",
    "Africa",
    "Middle East",
    "South Asia",
    "East Asia",
    "Oceania",
]

# Generate inner track data (regional GDP representation as percentage)
gdp_data = [26.0, 4.5, 22.0, 3.5, 5.0, 8.0, 28.0, 3.0]  # Approximate world GDP share %

# Create nodes with colors
nodes = [{"id": regions[i], "color": colors[i]} for i in range(n_regions)]

# Create inner track pie chart data (GDP representation)
inner_track_data = [{"name": region_full_names[i], "y": gdp_data[i], "color": colors[i]} for i in range(n_regions)]

# Create Highcharts configuration directly
chart_config = {
    "chart": {
        "type": "dependencywheel",
        "width": 3600,
        "height": 3600,
        "backgroundColor": "#ffffff",
        "marginRight": 420,
    },
    "title": {"text": "circos-basic · highcharts · pyplots.ai", "style": {"fontSize": "52px", "fontWeight": "bold"}},
    "subtitle": {"text": "Global Trade Flows Between Regions (with GDP Inner Track)", "style": {"fontSize": "36px"}},
    "accessibility": {"enabled": False},
    "credits": {"enabled": False},
    "tooltip": {"style": {"fontSize": "28px"}},
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "middle",
        "layout": "vertical",
        "itemStyle": {"fontSize": "32px", "fontWeight": "normal"},
        "symbolHeight": 28,
        "symbolWidth": 28,
        "symbolRadius": 14,
        "itemMarginTop": 18,
        "itemMarginBottom": 18,
        "x": -30,
        "title": {"text": "Regions", "style": {"fontSize": "36px", "fontWeight": "bold"}},
    },
    "plotOptions": {"dependencywheel": {"showInLegend": False}, "pie": {"showInLegend": False}},
    "series": [
        {
            "type": "dependencywheel",
            "name": "Trade Flow",
            "keys": ["from", "to", "weight"],
            "data": connections,
            "nodes": nodes,
            "size": "78%",
            "center": ["42%", "50%"],
            "dataLabels": {
                "enabled": True,
                "style": {"fontSize": "40px", "fontWeight": "bold", "textOutline": "5px white"},
                "distance": 50,
                "rotationMode": "circular",
                "padding": 8,
            },
            "nodeWidth": 45,
        },
        {
            "type": "pie",
            "name": "GDP Share",
            "data": inner_track_data,
            "size": "28%",
            "innerSize": "20%",
            "center": ["42%", "50%"],
            "showInLegend": False,
            "dataLabels": {
                "enabled": True,
                "format": "{point.percentage:.0f}%",
                "distance": -25,
                "style": {"fontSize": "22px", "fontWeight": "bold", "color": "#ffffff", "textOutline": "2px #333333"},
            },
            "tooltip": {"pointFormat": "<b>{point.name}</b>: {point.y}% of World GDP"},
        },
    ]
    + [
        {
            "type": "pie",
            "name": region_full_names[i],
            "data": [{"name": region_full_names[i], "y": 1, "color": colors[i]}],
            "size": 0,
            "showInLegend": True,
            "dataLabels": {"enabled": False},
        }
        for i in range(n_regions)
    ],
}

# Download Highcharts JS and sankey module (dependency wheel requires sankey)
highcharts_url = "https://code.highcharts.com/highcharts.js"
sankey_url = "https://code.highcharts.com/modules/sankey.js"
dependency_wheel_url = "https://code.highcharts.com/modules/dependency-wheel.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(sankey_url, timeout=30) as response:
    sankey_js = response.read().decode("utf-8")

with urllib.request.urlopen(dependency_wheel_url, timeout=30) as response:
    dependency_wheel_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
chart_config_json = json.dumps(chart_config)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{sankey_js}</script>
    <script>{dependency_wheel_js}</script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
        Highcharts.chart('container', {chart_config_json});
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save HTML for interactive version
interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>circos-basic · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/sankey.js"></script>
    <script src="https://code.highcharts.com/modules/dependency-wheel.js"></script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        Highcharts.chart('container', {chart_config_json});
    </script>
</body>
</html>"""
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(interactive_html)

# Setup Chrome for screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
