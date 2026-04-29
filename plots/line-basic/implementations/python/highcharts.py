""" anyplot.ai
line-basic: Basic Line Plot
Library: highcharts unknown | Python 3.13.13
Quality: 79/100 | Updated: 2026-04-29
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data - Monthly temperature readings with realistic irregular variation
np.random.seed(42)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
base_temps = [5, 7, 12, 16, 21, 25, 28, 27, 22, 15, 9, 6]
temperatures = [round(t + np.random.randn() * 1.5, 1) for t in base_temps]

# Chart configuration
chart_config = {
    "chart": {
        "type": "line",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginBottom": 300,
        "marginLeft": 250,
        "marginRight": 80,
        "spacingTop": 80,
    },
    "title": {
        "text": "line-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "72px", "fontWeight": "bold", "color": INK},
    },
    "xAxis": {
        "categories": month_labels,
        "title": {"text": "Month", "style": {"fontSize": "48px", "color": INK}, "margin": 30},
        "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}, "y": 40},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "lineWidth": 2,
        "tickWidth": 2,
    },
    "yAxis": {
        "title": {"text": "Temperature (°C)", "style": {"fontSize": "48px", "color": INK}, "margin": 30},
        "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}, "x": -10},
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "gridLineDashStyle": "Dash",
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
    "legend": {"enabled": False},
    "plotOptions": {"line": {"lineWidth": 8, "marker": {"enabled": True, "radius": 12, "symbol": "circle"}}},
    "series": [{"type": "line", "name": "Temperature", "data": temperatures, "color": BRAND}],
    "credits": {"enabled": False},
}

# Download Highcharts JS for inline embedding (fallback CDN on 403)
_hc_urls = [
    "https://code.highcharts.com/highcharts.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.3.0/highcharts.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js",
]
highcharts_js = None
for _url in _hc_urls:
    try:
        _req = urllib.request.Request(_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(_req, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if highcharts_js is None:
    raise RuntimeError("Could not download highcharts.js from any CDN")

# Build HTML with inline Highcharts JS
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>Highcharts.chart('container', {json.dumps(chart_config)});</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG
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
