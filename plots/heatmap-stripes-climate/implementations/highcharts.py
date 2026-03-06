""" pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: highcharts unknown | Python 3.14.3
Quality: 87/100 | Created: 2026-03-06
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.heatmap import HeatmapSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - synthetic global temperature anomalies (1850-2024) relative to 1961-1990 baseline
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

# Build a realistic warming trend: slight cooling until ~1910, flat until ~1970, then accelerating warming
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

# Symmetric color scale around 0
abs_max = float(max(abs(anomalies.min()), abs(anomalies.max())))

# Build heatmap data: [x, y, value] - fill multiple rows so stripes cover full height
n_rows = 30
series_data = [[i, row, round(float(anom), 4)] for row in range(n_rows) for i, anom in enumerate(anomalies)]

# Highcharts options using heatmap series with colorAxis (idiomatic Highcharts feature)
chart_options = {
    "chart": {
        "type": "heatmap",
        "width": 4800,
        "height": 1600,
        "backgroundColor": "#ffffff",
        "marginTop": -5,
        "marginLeft": -1,
        "marginRight": -1,
        "marginBottom": 70,
        "spacing": [0, 0, 0, 0],
    },
    "title": {
        "text": "heatmap-stripes-climate \u00b7 highcharts \u00b7 pyplots.ai",
        "align": "center",
        "verticalAlign": "bottom",
        "y": -15,
        "style": {"fontSize": "36px", "color": "#555555", "fontWeight": "normal"},
    },
    "colorAxis": {
        "min": -abs_max,
        "max": abs_max,
        "stops": [[0, "#08306b"], [0.25, "#4292c6"], [0.5, "#ffffff"], [0.75, "#ef3b2c"], [1, "#67000d"]],
        "visible": False,
    },
    "xAxis": {
        "visible": False,
        "lineWidth": 0,
        "lineColor": "transparent",
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

# Validate library usage via highcharts-core Python API
chart = Chart(container="container")
chart.options = HighchartsOptions()
chart.options.chart = {"type": "heatmap", "width": 4800, "height": 1600}
chart.options.color_axis = chart_options["colorAxis"]
series = HeatmapSeries()
series.name = "Temperature Anomaly"
series.data = [[0, 0, 0.1]]
chart.add_series(series)

# Serialize options as JSON (preserves data format for colorAxis mapping)
options_json = json.dumps(chart_options)

# Download Highcharts JS and heatmap module for inline embedding
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
heatmap_url = "https://cdn.jsdelivr.net/npm/highcharts@11/modules/heatmap.js"

req1 = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req1, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req2 = urllib.request.Request(heatmap_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req2, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width:4800px; height:1600px;"></div>
    <script>
        Highcharts.chart('container', {options_json});
    </script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with headless Chrome - larger window to capture title below stripes
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,1700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
