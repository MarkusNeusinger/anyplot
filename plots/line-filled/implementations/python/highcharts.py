"""anyplot.ai
line-filled: Filled Line Plot
Library: highcharts | Python 3.13
Quality: 91/100 | Updated: 2026-05-12
"""

import os
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data - Monthly website traffic over a year
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
base_traffic = 50000
seasonal = np.sin(np.linspace(0, 2 * np.pi, 12)) * 15000
noise = np.random.normal(0, 3000, 12)
traffic = base_traffic + seasonal + noise + np.linspace(0, 10000, 12)
traffic = np.maximum(traffic, 0).astype(int)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 220,
    "marginLeft": 150,
    "spacingTop": 40,
}

# Title
chart.options.title = {
    "text": "line-filled · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
}

# X-axis configuration
chart.options.x_axis = {
    "categories": months,
    "title": {"text": "Month", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Page Views", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "min": 0,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "16px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
}

# Plot options
chart.options.plot_options = {
    "area": {
        "fillOpacity": 0.4,
        "lineWidth": 3,
        "marker": {"enabled": True, "radius": 8, "lineWidth": 2, "lineColor": PAGE_BG},
        "states": {"hover": {"lineWidth": 4}},
    }
}

# Create series with Okabe-Ito brand color
series = AreaSeries()
series.name = "Website Traffic"
series.data = [int(v) for v in traffic]
series.color = BRAND
series.fill_color = {
    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
    "stops": [[0, "rgba(0, 158, 115, 0.4)"], [1, "rgba(0, 158, 115, 0.05)"]],
}

chart.add_series(series)

# Download Highcharts JS with retries
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_js = None
urls_to_try = [
    "https://code.highcharts.com/highcharts.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11.0.0/highcharts.js",
]

for url in urls_to_try:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url)
            req.add_header(
                "User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            )
            req.add_header("Accept", "*/*")
            req.add_header("Referer", "https://www.highcharts.com/")
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
                break
        except Exception:
            if attempt == 2:
                continue  # Try next URL
            time.sleep(2)
    if highcharts_js:
        break

if not highcharts_js:
    print("ERROR: Failed to download Highcharts library", file=sys.stderr)
    sys.exit(1)

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
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
