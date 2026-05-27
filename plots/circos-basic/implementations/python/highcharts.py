""" anyplot.ai
circos-basic: Circos Plot
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-15
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

# Data - Simulating trade flows between 8 chromosomes with expression tracks
np.random.seed(42)

chromosomes = ["Chr1", "Chr2", "Chr3", "Chr4", "Chr5", "Chr6", "Chr7", "Chr8"]

# Generate flow matrix - inter-chromosomal connections (similar to genomic translocations)
n_chrs = len(chromosomes)
flow_matrix = np.zeros((n_chrs, n_chrs))

for i in range(n_chrs):
    for j in range(n_chrs):
        if i != j:
            base_flow = np.random.exponential(40)
            # Some chr pairs have stronger connections (realistic genomic patterns)
            if (i == 0 and j == 6) or (i == 6 and j == 0):
                base_flow *= 3
            elif (i == 2 and j == 5) or (i == 5 and j == 2):
                base_flow *= 2.5
            elif (i == 1 and j == 4) or (i == 4 and j == 1):
                base_flow *= 2
            flow_matrix[i, j] = base_flow

# Filter connections for clarity
connections = []
for i in range(n_chrs):
    for j in range(n_chrs):
        if i != j and flow_matrix[i, j] > 15:
            connections.append([chromosomes[i], chromosomes[j], float(round(flow_matrix[i, j], 1))])

# Use Okabe-Ito palette for chromosomes (cycling through palette)
chr_colors = [IMPRINT[i % len(IMPRINT)] for i in range(n_chrs)]

# Create nodes with colors
nodes = [{"id": chromosomes[i], "color": chr_colors[i]} for i in range(n_chrs)]

# Create inner track data (expression values as percentages)
expression_data = [28.0, 19.0, 16.0, 13.0, 10.0, 7.0, 5.0, 2.0]

inner_track_data = [{"name": chromosomes[i], "y": expression_data[i], "color": chr_colors[i]} for i in range(n_chrs)]

# Create Highcharts configuration with theme-adaptive colors
chart_config = {
    "chart": {
        "type": "dependencywheel",
        "width": 3600,
        "height": 3600,
        "backgroundColor": PAGE_BG,
        "marginRight": 500,
        "style": {"color": INK},
    },
    "title": {
        "text": "circos-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "52px", "fontWeight": "bold", "color": INK},
    },
    "subtitle": {
        "text": "Chromosomal Connections with Expression Tracks",
        "style": {"fontSize": "32px", "color": INK_SOFT},
    },
    "accessibility": {"enabled": False},
    "credits": {"enabled": False},
    "tooltip": {"style": {"fontSize": "20px", "color": INK}},
    "legend": {
        "enabled": True,
        "align": "right",
        "verticalAlign": "middle",
        "layout": "vertical",
        "itemStyle": {"fontSize": "24px", "color": INK_SOFT},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 2,
        "symbolHeight": 24,
        "symbolWidth": 24,
        "symbolRadius": 12,
        "itemMarginTop": 16,
        "itemMarginBottom": 16,
        "x": -50,
        "title": {"text": "Chromosomes", "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK}},
    },
    "plotOptions": {"dependencywheel": {"showInLegend": False}, "pie": {"showInLegend": False}},
    "colors": IMPRINT,
    "series": [
        {
            "type": "dependencywheel",
            "name": "Connections",
            "keys": ["from", "to", "weight"],
            "data": connections,
            "nodes": nodes,
            "size": "72%",
            "center": ["35%", "50%"],
            "dataLabels": {
                "enabled": True,
                "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK, "textOutline": f"3px {PAGE_BG}"},
                "distance": 30,
                "rotationMode": "circular",
                "padding": 6,
            },
            "nodeWidth": 50,
            "nodeColor": "#ffffff",
        },
        {
            "type": "pie",
            "name": "Expression",
            "data": inner_track_data,
            "size": "32%",
            "innerSize": "24%",
            "center": ["35%", "50%"],
            "showInLegend": False,
            "dataLabels": {
                "enabled": True,
                "format": "{point.percentage:.0f}%",
                "distance": -20,
                "style": {"fontSize": "24px", "fontWeight": "bold", "color": INK, "textOutline": f"2px {PAGE_BG}"},
            },
            "tooltip": {"pointFormat": "<b>{point.name}</b>: {point.y:.1f}%"},
        },
    ]
    + [
        {
            "type": "pie",
            "name": chromosomes[i],
            "data": [{"name": chromosomes[i], "y": 1, "color": chr_colors[i]}],
            "size": 0,
            "showInLegend": True,
            "dataLabels": {"enabled": False},
        }
        for i in range(n_chrs)
    ],
}

# Download Highcharts JS modules from CDN
highcharts_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/highcharts.js"
sankey_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/modules/sankey.min.js"
dependency_wheel_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.4.8/modules/dependency-wheel.min.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(sankey_url, timeout=30) as response:
    sankey_js = response.read().decode("utf-8")

with urllib.request.urlopen(dependency_wheel_url, timeout=30) as response:
    dependency_wheel_js = response.read().decode("utf-8")

# Generate HTML with inline scripts for PNG export
chart_config_json = json.dumps(chart_config)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{sankey_js}</script>
    <script>{dependency_wheel_js}</script>
</head>
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
        Highcharts.chart('container', {chart_config_json});
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot for PNG
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Setup Chrome for screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3600, "height": 3600, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Generate HTML with CDN links for interactive version
interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>circos-basic · highcharts · anyplot.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/sankey.js"></script>
    <script src="https://code.highcharts.com/modules/dependency-wheel.js"></script>
</head>
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        Highcharts.chart('container', {chart_config_json});
    </script>
</body>
</html>"""
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(interactive_html)
