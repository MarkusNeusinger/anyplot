""" anyplot.ai
radar-basic: Basic Radar Chart
Library: highcharts unknown | Python 3.13.13
Quality: 76/100 | Updated: 2026-04-29
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - Employee performance metrics comparison
categories = ["Communication", "Technical Skills", "Teamwork", "Problem Solving", "Leadership", "Creativity"]
employee_a_values = [70, 95, 75, 90, 65, 80]
employee_b_values = [90, 70, 95, 75, 85, 70]

# Chart config (polar/radar via JSON)
chart_config = {
    "chart": {"polar": True, "width": 4800, "height": 2700, "backgroundColor": PAGE_BG, "style": {"color": INK}},
    "title": {
        "text": "radar-basic · highcharts · anyplot.ai",
        "style": {"fontSize": "72px", "fontWeight": "bold", "color": INK},
    },
    "xAxis": {
        "categories": categories,
        "tickmarkPlacement": "on",
        "lineWidth": 0,
        "labels": {"style": {"fontSize": "40px", "color": INK_SOFT}},
    },
    "yAxis": {
        "gridLineInterpolation": "polygon",
        "lineWidth": 0,
        "min": 0,
        "max": 100,
        "tickInterval": 20,
        "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}},
        "gridLineWidth": 2,
        "gridLineColor": GRID,
    },
    "pane": {"size": "75%"},
    "plotOptions": {
        "series": {"pointPlacement": "on"},
        "area": {"fillOpacity": 0.25, "lineWidth": 4, "marker": {"enabled": True, "radius": 12}},
    },
    "legend": {
        "enabled": True,
        "align": "center",
        "verticalAlign": "bottom",
        "layout": "horizontal",
        "itemStyle": {"fontSize": "36px", "color": INK_SOFT},
        "backgroundColor": ELEVATED_BG,
    },
    "series": [
        {"type": "area", "name": "Employee A", "data": employee_a_values, "color": OKABE_ITO[0], "fillOpacity": 0.25},
        {"type": "area", "name": "Employee B", "data": employee_b_values, "color": OKABE_ITO[1], "fillOpacity": 0.25},
    ],
    "credits": {"enabled": False},
}


_hc_urls = [
    "https://code.highcharts.com/highcharts.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.3.0/highcharts.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js",
]
highcharts_js = None
for _url in _hc_urls:
    try:
        _req = urllib.request.Request(_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(_req, timeout=30) as _resp:
            highcharts_js = _resp.read().decode("utf-8")
        break
    except Exception:
        continue
if highcharts_js is None:
    raise RuntimeError("Could not download highcharts.js from any CDN")

_hc_more_urls = [
    "https://code.highcharts.com/highcharts-more.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.3.0/highcharts-more.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js",
]
highcharts_more_js = None
for _url in _hc_more_urls:
    try:
        _req = urllib.request.Request(_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(_req, timeout=30) as _resp:
            highcharts_more_js = _resp.read().decode("utf-8")
        break
    except Exception:
        continue
if highcharts_more_js is None:
    raise RuntimeError("Could not download highcharts-more.js from any CDN")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:4800px; height:2700px;"></div>
    <script>Highcharts.chart('container', {json.dumps(chart_config)});</script>
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
