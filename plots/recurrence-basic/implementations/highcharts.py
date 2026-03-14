""" pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: highcharts unknown | Python 3.14.3
Quality: 76/100 | Created: 2026-03-14
"""

import json
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Logistic map near onset of chaos (r=3.82)
np.random.seed(42)
n_steps = 300
r = 3.82
series = np.zeros(n_steps)
series[0] = 0.1
for i in range(1, n_steps):
    series[i] = r * series[i - 1] * (1 - series[i - 1])

# Time-delay embedding (Takens' theorem)
embedding_dim = 3
delay = 1
n_embedded = n_steps - (embedding_dim - 1) * delay
embedded = np.array([series[i : i + embedding_dim * delay : delay] for i in range(n_embedded)])

# Compute distance matrix and apply threshold for binary recurrence
distance_matrix = cdist(embedded, embedded, metric="euclidean")
threshold = 0.15 * np.max(distance_matrix)
recurrence_matrix = (distance_matrix <= threshold).astype(int)

# Prepare heatmap data: [x, y, value] for recurrent points only
data = []
for i in range(n_embedded):
    for j in range(n_embedded):
        if recurrence_matrix[i, j] == 1:
            data.append([j, i, 1])

# Chart options
chart_options = {
    "chart": {
        "type": "heatmap",
        "width": 3600,
        "height": 3600,
        "backgroundColor": "#ffffff",
        "marginTop": 150,
        "marginBottom": 200,
        "marginLeft": 250,
        "marginRight": 100,
    },
    "title": {
        "text": "Logistic Map (r=3.82) \u00b7 recurrence-basic \u00b7 highcharts \u00b7 pyplots.ai",
        "style": {"fontSize": "44px", "fontWeight": "500"},
    },
    "xAxis": {
        "title": {"text": "Time Index (i)", "style": {"fontSize": "32px", "color": "#333333"}},
        "labels": {"style": {"fontSize": "22px"}},
        "min": 0,
        "max": n_embedded - 1,
        "gridLineWidth": 0,
        "lineWidth": 2,
        "lineColor": "#333333",
        "tickWidth": 0,
    },
    "yAxis": {
        "title": {"text": "Time Index (j)", "style": {"fontSize": "32px", "color": "#333333"}},
        "labels": {"style": {"fontSize": "22px"}},
        "min": 0,
        "max": n_embedded - 1,
        "reversed": True,
        "gridLineWidth": 0,
        "lineWidth": 2,
        "lineColor": "#333333",
        "tickWidth": 0,
    },
    "colorAxis": {"min": 0, "max": 1, "stops": [[0, "#ffffff"], [1, "#306998"]], "visible": False},
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "tooltip": {
        "headerFormat": "",
        "pointFormat": "Time i: <b>{point.x}</b><br>Time j: <b>{point.y}</b>",
        "style": {"fontSize": "20px"},
    },
    "plotOptions": {"heatmap": {"borderWidth": 0, "colsize": 1, "rowsize": 1, "nullColor": "#ffffff"}},
    "series": [
        {"type": "heatmap", "name": "Recurrence", "data": data, "color": "#306998", "dataLabels": {"enabled": False}}
    ],
}

# Download Highcharts JS and heatmap module with fallback CDNs
cdn_bases = ["https://code.highcharts.com", "https://cdn.jsdelivr.net/npm/highcharts@11"]


js_modules = {"highcharts": "/highcharts.js", "heatmap": "/modules/heatmap.js"}
js_code = {}

for name, path in js_modules.items():
    for base in cdn_bases:
        try:
            req = urllib.request.Request(base + path, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                js_code[name] = response.read().decode("utf-8")
            break
        except Exception:
            continue

highcharts_js = js_code["highcharts"]
heatmap_js = js_code["heatmap"]

# Convert options to JSON
options_json = json.dumps(chart_options)

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
        Highcharts.chart('container', {options_json});
    </script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot using headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
