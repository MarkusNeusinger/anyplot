""" anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: highcharts unknown | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-13
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


# Theme-adaptive colors
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette - first series is always #009E73
BRAND = "#009E73"

# Data - Tech companies with market metrics
np.random.seed(42)
companies = [
    "TechCorp",
    "DataFlow",
    "CloudNet",
    "ByteWorks",
    "NeuralSys",
    "QuantumIO",
    "CyberEdge",
    "AlphaCore",
    "OmniSoft",
    "GridLogic",
    "NovaCode",
    "SyncLabs",
    "PrimeData",
    "VectorAI",
    "CoreStack",
]
revenue = np.random.uniform(50, 500, 15)
growth = revenue * 0.12 + np.random.normal(0, 15, 15)

# Create data points with names (labels)
data_points = [
    {"x": round(float(revenue[i]), 1), "y": round(float(growth[i]), 1), "name": companies[i]}
    for i in range(len(companies))
]

# Build Highcharts configuration
chart_config = {
    "chart": {
        "type": "scatter",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginBottom": 280,
        "marginTop": 120,
        "marginLeft": 220,
        "marginRight": 200,
    },
    "title": {
        "text": "scatter-annotated · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "500", "color": INK},
    },
    "xAxis": {
        "title": {"text": "Annual Revenue ($ millions)", "style": {"fontSize": "22px", "color": INK}, "margin": 30},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
        "gridLineWidth": 1,
        "min": 0,
        "max": 550,
        "tickInterval": 100,
    },
    "yAxis": {
        "title": {"text": "Year-over-Year Growth (%)", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
        "gridLineWidth": 1,
    },
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "plotOptions": {
        "scatter": {
            "marker": {"radius": 8, "fillColor": BRAND},
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "style": {"fontSize": "18px", "fontWeight": "500", "textOutline": "2px " + PAGE_BG, "color": INK},
                "y": -30,
                "allowOverlap": False,
            },
        }
    },
    "series": [{"type": "scatter", "name": "Companies", "color": BRAND, "data": data_points}],
}

# Download Highcharts JS from jsDelivr CDN
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
chart_json = json.dumps(chart_config)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            Highcharts.chart('container', {chart_json});
        }});
    </script>
</body>
</html>"""

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML with theme-suffixed name
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Setup headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

# Take screenshot
driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Cleanup
Path(temp_path).unlink()
