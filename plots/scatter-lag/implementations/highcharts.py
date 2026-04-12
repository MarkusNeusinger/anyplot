""" pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: highcharts unknown | Python 3.14.3
Quality: 88/100 | Created: 2026-04-12
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data — synthetic AR(1) process with strong positive autocorrelation
np.random.seed(42)
n = 300
phi = 0.85
noise = np.random.normal(0, 1, n)
temperature = np.zeros(n)
temperature[0] = 20.0
for i in range(1, n):
    temperature[i] = 20 + phi * (temperature[i - 1] - 20) + noise[i]

# Lag plot data: y(t) vs y(t+1)
lag = 1
yt = temperature[:-lag]
yt_lag = temperature[lag:]
time_index = np.arange(len(yt))

# Correlation coefficient
r_value = np.corrcoef(yt, yt_lag)[0, 1]

# Axis bounds
pad = 0.5
all_vals = np.concatenate([yt, yt_lag])
axis_min = float(np.floor(all_vals.min() - pad))
axis_max = float(np.ceil(all_vals.max() + pad))

# Color points by time index — early=light, late=dark using Python Blue palette
n_points = len(yt)
colors = []
for i in range(n_points):
    t = i / (n_points - 1)
    r = int(48 + (180 - 48) * (1 - t))
    g = int(105 + (210 - 105) * (1 - t))
    b = int(152 + (230 - 152) * (1 - t))
    alpha = 0.4 + 0.45 * t
    colors.append(f"rgba({r}, {g}, {b}, {alpha:.2f})")

# Build scatter data with per-point color
scatter_data = []
for i in range(n_points):
    scatter_data.append({"x": float(yt[i]), "y": float(yt_lag[i]), "color": colors[i]})

# Diagonal reference line (y = x)
diag_data = [[axis_min, axis_min], [axis_max, axis_max]]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginTop": 160,
    "marginBottom": 300,
    "marginLeft": 260,
    "marginRight": 200,
}

chart.options.title = {
    "text": "scatter-lag \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "600", "color": "#2c3e50", "letterSpacing": "1px"},
    "margin": 50,
}

chart.options.subtitle = {
    "text": f"AR(1) Temperature Series \u2014 Lag {lag} Autocorrelation (r = {r_value:.3f})",
    "style": {"fontSize": "38px", "color": "#7f8c8d", "fontWeight": "400"},
}

chart.options.x_axis = {
    "title": {"text": "y(t)", "style": {"fontSize": "44px", "color": "#34495e", "fontWeight": "500"}, "margin": 30},
    "labels": {"style": {"fontSize": "34px", "color": "#7f8c8d"}},
    "min": axis_min,
    "max": axis_max,
    "tickInterval": 2,
    "startOnTick": False,
    "endOnTick": False,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#bdc3c7",
    "lineWidth": 2,
    "tickColor": "#bdc3c7",
    "tickLength": 10,
}

chart.options.y_axis = {
    "title": {
        "text": f"y(t+{lag})",
        "style": {"fontSize": "44px", "color": "#34495e", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#7f8c8d"}},
    "min": axis_min,
    "max": axis_max,
    "tickInterval": 2,
    "startOnTick": False,
    "endOnTick": False,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#bdc3c7",
    "lineWidth": 2,
    "tickColor": "#bdc3c7",
    "tickLength": 10,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 80,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.85)",
    "borderWidth": 1,
    "borderColor": "#e0e0e0",
    "borderRadius": 8,
    "itemStyle": {"fontSize": "30px", "fontWeight": "400", "color": "#34495e"},
    "padding": 16,
    "symbolRadius": 6,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:24px;color:{point.color}">\u25cf</span> '
        '<span style="font-size:26px">'
        "y(t): <b>{point.x:.2f}</b><br/>"
        f"y(t+{lag}): <b>{{point.y:.2f}}</b></span>"
    ),
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 10,
    "borderWidth": 2,
    "shadow": {"color": "rgba(0,0,0,0.1)", "offsetX": 2, "offsetY": 2, "width": 4},
    "style": {"fontSize": "26px"},
}

# Scatter series — colored by time index
scatter = ScatterSeries()
scatter.data = scatter_data
scatter.name = f"Lag {lag} pairs"
scatter.marker = {
    "radius": 10,
    "symbol": "circle",
    "lineWidth": 1.5,
    "lineColor": "#ffffff",
    "states": {"hover": {"radiusPlus": 4, "lineWidthPlus": 1, "lineColor": "#306998"}},
}
scatter.z_index = 2

# Diagonal reference line (y = x)
diag_line = SplineSeries()
diag_line.data = diag_data
diag_line.name = "y = x reference"
diag_line.color = "rgba(149, 165, 166, 0.6)"
diag_line.line_width = 3
diag_line.dash_style = "LongDash"
diag_line.marker = {"enabled": False}
diag_line.enable_mouse_tracking = False
diag_line.z_index = 1

chart.add_series(scatter)
chart.add_series(diag_line)

# Export
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

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

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
