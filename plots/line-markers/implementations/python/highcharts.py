""" anyplot.ai
line-markers: Line Plot with Markers
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-12
"""

import base64
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

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Stock price tracking with different patterns
np.random.seed(42)
days = np.arange(0, 60)

# Three stocks with distinct patterns
stock_a = 100 + 0.5 * days + np.random.normal(0, 1, 60)
stock_b = 95 + np.cumsum(np.random.normal(0, 2, 60))
stock_c = 110 + 0.1 * days + np.random.normal(0, 0.8, 60)

# Prepare chart configuration
chart_config = {
    "chart": {
        "type": "line",
        "width": 4800,
        "height": 2700,
        "backgroundColor": PAGE_BG,
        "marginBottom": 250,
        "marginLeft": 180,
        "spacingBottom": 50,
        "style": {"color": INK},
    },
    "colors": IMPRINT,
    "title": {"text": "line-markers · highcharts · anyplot.ai", "style": {"fontSize": "28px", "color": INK}},
    "xAxis": {
        "title": {"text": "Day", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
        "min": 0,
        "max": 59,
    },
    "yAxis": {
        "title": {"text": "Price ($)", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineWidth": 1,
        "gridLineColor": GRID,
    },
    "legend": {
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
    },
    "plotOptions": {
        "line": {"lineWidth": 3, "marker": {"enabled": True, "radius": 8, "lineWidth": 2, "lineColor": PAGE_BG}}
    },
    "series": [
        {
            "name": "Stock A",
            "data": [[int(d), round(float(p), 1)] for d, p in zip(days, stock_a, strict=False)],
            "color": IMPRINT[0],
            "marker": {"symbol": "circle", "fillColor": IMPRINT[0]},
        },
        {
            "name": "Stock B",
            "data": [[int(d), round(float(p), 1)] for d, p in zip(days, stock_b, strict=False)],
            "color": IMPRINT[1],
            "marker": {"symbol": "diamond", "fillColor": IMPRINT[1]},
        },
        {
            "name": "Stock C",
            "data": [[int(d), round(float(p), 1)] for d, p in zip(days, stock_c, strict=False)],
            "color": IMPRINT[2],
            "marker": {"symbol": "triangle", "fillColor": IMPRINT[2]},
        },
    ],
}


def download_js(urls, timeout=30, max_retries=3):
    if not isinstance(urls, list):
        urls = [urls]

    for url in urls:
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    return response.read().decode("utf-8")
            except Exception:
                if attempt == max_retries - 1:
                    continue
                time.sleep(1)

    raise RuntimeError("Failed to download Highcharts JS from all sources")


highcharts_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11.4.3/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
]
highcharts_js = download_js(highcharts_urls)

# Generate HTML with inline scripts
js_config = json.dumps(chart_config)
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
        Highcharts.chart('container', {js_config});
    }});
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

screenshot_config = {"captureBeyondViewport": True, "clip": {"x": 0, "y": 0, "width": 4800, "height": 2700, "scale": 1}}
result = driver.execute_cdp_cmd("Page.captureScreenshot", screenshot_config)
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(base64.b64decode(result["data"]))
driver.quit()

Path(temp_path).unlink()
