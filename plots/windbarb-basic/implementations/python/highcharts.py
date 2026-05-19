"""anyplot.ai
windbarb-basic: Wind Barb Plot for Meteorological Data
Library: highcharts_core | Python 3.13
Quality: pending | Created: 2026-05-19
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
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

# Data: Surface wind observations from weather station transect
np.random.seed(42)
n_stations = 20

# u (east-west) and v (north-south) wind components in m/s
u = 8 + 6 * np.sin(np.linspace(0, 2 * np.pi, n_stations)) + np.random.randn(n_stations) * 2
v = 4 + 4 * np.cos(np.linspace(0, 1.5 * np.pi, n_stations)) + np.random.randn(n_stations) * 2

speed_ms = np.sqrt(u**2 + v**2)
speed_knots = speed_ms * 1.94384
# Meteorological convention: direction FROM which wind blows
direction = (270 - np.degrees(np.arctan2(v, u))) % 360

# Object format preserves y-position: barbs render at their wind speed on the y-axis
data_points = [
    {
        "x": i,
        "y": round(float(speed_knots[i]), 1),
        "value": round(float(speed_knots[i]), 1),
        "direction": round(float(direction[i]), 0),
    }
    for i in range(n_stations)
]

# Chart structure using highcharts_core Python API (all options except series)
chart = Chart(container="container")
chart.options = HighchartsOptions.from_dict(
    {
        "chart": {
            "width": 4800,
            "height": 2700,
            "backgroundColor": PAGE_BG,
            "marginBottom": 200,
            "marginLeft": 250,
            "marginRight": 150,
            "marginTop": 180,
        },
        "title": {
            "text": "windbarb-basic · python · highcharts · anyplot.ai",
            "style": {"fontSize": "56px", "fontWeight": "bold", "color": INK},
        },
        "xAxis": {
            "title": {"text": "Weather Station Index", "style": {"fontSize": "40px", "color": INK}, "margin": 24},
            "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}},
            "lineColor": INK_SOFT,
            "tickColor": INK_SOFT,
            "tickInterval": 2,
            "gridLineColor": GRID,
        },
        "yAxis": {
            "title": {"text": "Wind Speed (knots)", "style": {"fontSize": "40px", "color": INK}},
            "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}},
            "min": 0,
            "max": 40,
            "tickInterval": 5,
            "gridLineColor": GRID,
            "lineColor": INK_SOFT,
        },
        "legend": {"enabled": False},
        "tooltip": {"style": {"fontSize": "28px"}, "pointFormat": "Wind: {point.value} kn from {point.direction}°"},
        "plotOptions": {"windbarb": {"vectorLength": 80, "lineWidth": 6}},
        "credits": {"enabled": False},
    }
)

# Generate chart JS via Python library, then inject windbarb series with object-format
# data so Highcharts uses the `y` property for per-barb vertical positioning.
# (highcharts_core serialises dict points to arrays which drops y; raw JSON preserves it.)
chart_js_base = chart.to_js_literal()
series_json = json.dumps(
    [
        {
            "type": "windbarb",
            "name": "Surface Wind",
            "color": BRAND,
            "vectorLength": 80,
            "lineWidth": 6,
            "data": data_points,
        }
    ]
)
CLOSING = "\n},\n);\n});"
chart_js = chart_js_base[: -len(CLOSING)] + f",\n  series: {series_json}" + CLOSING

# Download Highcharts JS modules inline (required for headless Chrome file:// loading)
modules = {}
for name, url in [
    ("highcharts", "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"),
    ("more", "https://cdn.jsdelivr.net/npm/highcharts/highcharts-more.js"),
    ("datagrouping", "https://cdn.jsdelivr.net/npm/highcharts/modules/datagrouping.js"),
    ("windbarb", "https://cdn.jsdelivr.net/npm/highcharts/modules/windbarb.js"),
]:
    with urllib.request.urlopen(url, timeout=30) as resp:
        modules[name] = resp.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{modules["highcharts"]}</script>
    <script>{modules["more"]}</script>
    <script>{modules["datagrouping"]}</script>
    <script>{modules["windbarb"]}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Save PNG via Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4900, 2800)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
