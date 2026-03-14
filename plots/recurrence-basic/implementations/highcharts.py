"""pyplots.ai
recurrence-basic: Recurrence Plot for Nonlinear Time Series
Library: highcharts unknown | Python 3.14.3
Quality: 76/100 | Created: 2026-03-14
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

# Distance matrix with normalized values for continuous color mapping
distance_matrix = cdist(embedded, embedded, metric="euclidean")
threshold = 0.15 * np.max(distance_matrix)

# Prepare heatmap data using vectorized approach: [x, y, normalized_distance]
# Use continuous distance values (capped at threshold) for visual depth
recurrent = np.argwhere(distance_matrix <= threshold)
norm_distances = distance_matrix[recurrent[:, 0], recurrent[:, 1]] / threshold
data = [[int(pt[1]), int(pt[0]), round(1.0 - float(norm_distances[idx]), 4)] for idx, pt in enumerate(recurrent)]

# Build chart using highcharts_core API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "heatmap",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#fafafa",
    "marginTop": 200,
    "marginBottom": 280,
    "marginLeft": 240,
    "marginRight": 160,
    "style": {"fontFamily": "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {
    "text": "recurrence-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "600", "color": "#1a1a2e"},
    "y": 50,
}

chart.options.subtitle = {
    "text": (
        "Logistic Map (r=3.82) \u2014 Takens Embedding (d=3, \u03c4=1) "
        f"\u2014 \u03b5={threshold:.3f} \u2014 {n_embedded} time steps"
    ),
    "style": {"fontSize": "32px", "fontWeight": "400", "color": "#555555"},
    "y": 110,
}

chart.options.x_axis = {
    "title": {
        "text": "Time Index (i)",
        "style": {"fontSize": "36px", "color": "#1a1a2e", "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "24px", "color": "#444444"}},
    "min": 0,
    "max": n_embedded - 1,
    "gridLineWidth": 0,
    "lineWidth": 2,
    "lineColor": "#1a1a2e",
    "tickWidth": 0,
    "tickInterval": 50,
}

chart.options.y_axis = {
    "title": {
        "text": "Time Index (j)",
        "style": {"fontSize": "36px", "color": "#1a1a2e", "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "24px", "color": "#444444"}},
    "min": 0,
    "max": n_embedded - 1,
    "reversed": True,
    "gridLineWidth": 0,
    "lineWidth": 2,
    "lineColor": "#1a1a2e",
    "tickWidth": 0,
    "tickInterval": 50,
}

# Continuous colorAxis: distance-based gradient for visual depth
chart.options.color_axis = {
    "min": 0,
    "max": 1,
    "stops": [[0, "#e8eaf6"], [0.3, "#5c6bc0"], [0.6, "#283593"], [1.0, "#0d1b3e"]],
    "labels": {"style": {"fontSize": "22px", "color": "#444444"}, "format": "{value:.1f}"},
    "title": {"text": "Recurrence Strength", "style": {"fontSize": "24px", "color": "#1a1a2e"}},
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "symbolHeight": 400,
    "symbolWidth": 24,
    "margin": 20,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:18px">'
        "Time i: <b>{point.x}</b><br>"
        "Time j: <b>{point.y}</b><br>"
        "Strength: <b>{point.value:.2f}</b>"
        "</span>"
    ),
}

chart.options.plot_options = {"heatmap": {"borderWidth": 0, "colsize": 1, "rowsize": 1, "nullColor": "#fafafa"}}

# Add series using highcharts_core API
heatmap_series = HeatmapSeries()
heatmap_series.data = data
heatmap_series.name = "Recurrence"
chart.add_series(heatmap_series)

# Download Highcharts JS modules for rendering
cdn_bases = ["https://code.highcharts.com", "https://cdn.jsdelivr.net/npm/highcharts@11"]
js_paths = {"highcharts": "/highcharts.js", "heatmap": "/modules/heatmap.js"}
js_code = {}
for name, path in js_paths.items():
    for base in cdn_bases:
        try:
            req = urllib.request.Request(base + path, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                js_code[name] = resp.read().decode("utf-8")
            break
        except Exception:
            continue

highcharts_js = js_code["highcharts"]
heatmap_js = js_code["heatmap"]

# Export chart options via highcharts_core API and render directly
options_json = json.dumps(chart.options.to_dict())

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; background:#fafafa;">
    <div id="container" style="width:3600px; height:3600px;"></div>
    <script>Highcharts.chart('container', {options_json});</script>
</body>
</html>"""

# Save interactive HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Render PNG via headless Chrome
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
