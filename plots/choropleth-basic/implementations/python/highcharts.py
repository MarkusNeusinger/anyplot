"""anyplot.ai
choropleth-basic: Choropleth Map with Regional Coloring
Library: highcharts | Python 3.13
Quality: pending | Created: 2025-05-15
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
    "chart": {"map": None, "width": 4800, "height": 2700, "backgroundColor": PAGE_BG, "spacing": [80, 100, 80, 80]},
    "title": {
        "text": "choropleth-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
        "y": 40,
    },
    "subtitle": {
        "text": "Population Density (people per km²)",
        "style": {"fontSize": "22px", "color": INK_SOFT},
        "y": 90,
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
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "title": {"text": "Density (per km²)", "style": {"fontSize": "22px", "color": INK}},
    },
    "legend": {
        "layout": "vertical",
        "align": "right",
        "verticalAlign": "middle",
        "floating": False,
        "backgroundColor": ELEVATED_BG,
        "padding": 24,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "symbolHeight": 400,
        "symbolWidth": 28,
        "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
        "title": {"text": "Density<br/>(per km²)", "style": {"fontSize": "22px", "color": INK}},
    },
    "tooltip": {
        "style": {"fontSize": "18px", "color": INK},
        "headerFormat": "",
        "pointFormat": "<b>{point.name}</b><br/>Density: {point.value} per km²",
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
                "style": {
                    "fontSize": "16px",
                    "color": INK,
                    "textOutline": "2px #FFFFFF" if THEME == "light" else "2px #1A1A17",
                },
            },
            "borderColor": INK_SOFT,
            "borderWidth": 2,
            "nullColor": "#e8e8e8" if THEME == "light" else "#5a5a57",
        }
    ],
}

# Convert to JSON for JavaScript
chart_json = json.dumps(chart_config)

# Download required JavaScript files
highcharts_url = "https://code.highcharts.com/maps/highmaps.js"
europe_url = "https://code.highcharts.com/mapdata/custom/europe.topo.json"

headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.highcharts.com/"}
req_hc = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(req_hc, timeout=60) as response:
    highmaps_js = response.read().decode("utf-8")

req_eu = urllib.request.Request(europe_url, headers=headers)
with urllib.request.urlopen(req_eu, timeout=60) as response:
    europe_topo = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highmaps_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
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
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
time.sleep(6)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
