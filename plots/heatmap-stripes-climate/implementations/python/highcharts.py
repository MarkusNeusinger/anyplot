""" anyplot.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-06-02
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
MIDPOINT = "#FAF8F1" if THEME == "light" else "#1A1A17"  # imprint_div midpoint

# Data - synthetic global temperature anomalies (1850-2024) relative to 1961-1990 baseline
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

base_trend = np.piecewise(
    years.astype(float),
    [years < 1910, (years >= 1910) & (years < 1970), years >= 1970],
    [
        lambda y: -0.3 + (y - 1850) * (-0.002),
        lambda y: -0.15 + (y - 1910) * 0.002,
        lambda y: -0.03 + (y - 1970) * 0.022,
    ],
)
noise = np.random.normal(0, 0.08, n_years)
anomalies = base_trend + noise

abs_max = float(max(abs(anomalies.min()), abs(anomalies.max())))

# Build heatmap data: [x_index, y_row, value] — 50 rows fill full canvas height
n_rows = 50
series_data = [[i, row, round(float(anom), 4)] for row in range(n_rows) for i, anom in enumerate(anomalies)]

title = "heatmap-stripes-climate · python · highcharts · anyplot.ai"

chart_options = {
    "chart": {
        "type": "heatmap",
        "width": 3200,
        "height": 1800,
        "backgroundColor": PAGE_BG,
        "marginTop": 0,
        "marginLeft": 0,
        "marginRight": 0,
        "marginBottom": 75,
        "spacing": [0, 0, 0, 0],
    },
    "title": {
        "text": title,
        "align": "center",
        "verticalAlign": "bottom",
        "y": -12,
        "style": {"fontSize": "66px", "color": INK_SOFT, "fontWeight": "normal"},
    },
    "colorAxis": {
        "min": -abs_max,
        "max": abs_max,
        "stops": [
            [0, "#4467A3"],  # Imprint blue — cold / negative anomaly
            [0.5, MIDPOINT],  # theme-adaptive neutral midpoint (near-zero years)
            [1, "#AE3030"],  # Imprint matte red — warm / positive anomaly
        ],
        "visible": False,
    },
    "xAxis": {
        "visible": False,
        "lineWidth": 0,
        "tickLength": 0,
        "min": -0.5,
        "max": n_years - 0.5,
        "startOnTick": False,
        "endOnTick": False,
        "minPadding": 0,
        "maxPadding": 0,
    },
    "yAxis": {
        "visible": False,
        "lineWidth": 0,
        "gridLineWidth": 0,
        "min": -0.5,
        "max": n_rows - 0.5,
        "startOnTick": False,
        "endOnTick": False,
        "minPadding": 0,
        "maxPadding": 0,
    },
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "plotOptions": {
        "heatmap": {"colsize": 1, "rowsize": 1, "borderWidth": 0, "animation": False},
        "series": {"enableMouseTracking": False},
    },
    "tooltip": {"enabled": False},
    "series": [
        {
            "type": "heatmap",
            "name": "Temperature Anomaly",
            "data": series_data,
            "colsize": 1,
            "rowsize": 1,
            "borderWidth": 0,
        }
    ],
}

options_json = json.dumps(chart_options)

# Download Highcharts JS and heatmap module for inline embedding (CDN blocked in headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts@11/modules/heatmap.js"

req1 = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req1, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req2 = urllib.request.Request(heatmap_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>html, body {{ margin: 0; padding: 0; overflow: hidden; }}</style>
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="background:{PAGE_BG};">
    <div id="container" style="width:3200px; height:1800px;"></div>
    <script>
        Highcharts.chart('container', {options_json});
    </script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone loses ~139 px to Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact 3200×1800 — absorbs any ±1–2 px rounding from headless Chrome
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
