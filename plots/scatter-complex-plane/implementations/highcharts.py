""" pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: highcharts unknown | Python 3.14.3
Quality: 78/100 | Created: 2026-03-04
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


# Data — complex numbers for an Argand diagram
# 3rd roots of unity: e^(2πik/3) for k = 0, 1, 2
n_roots = 3
angles_roots = [2 * np.pi * k / n_roots for k in range(n_roots)]
roots_real = [np.cos(a) for a in angles_roots]
roots_imag = [np.sin(a) for a in angles_roots]
roots_labels = [f"ω{k}" for k in range(n_roots)]

# Arbitrary complex numbers
arb_points = [
    (2.0, 1.5, "z₁ = 2+1.5i"),
    (-1.2, 2.0, "z₂ = −1.2+2i"),
    (1.5, -1.8, "z₃ = 1.5−1.8i"),
    (-2.0, -1.0, "z₄ = −2−i"),
    (0.5, 2.5, "z₅ = 0.5+2.5i"),
]
arb_real = [p[0] for p in arb_points]
arb_imag = [p[1] for p in arb_points]
arb_labels = [p[2] for p in arb_points]

# Sum of roots of unity (should be ~0)
sum_real = sum(roots_real)
sum_imag = sum(roots_imag)

# Unit circle points
theta = np.linspace(0, 2 * np.pi, 200)
circle_x = np.cos(theta).tolist()
circle_y = np.sin(theta).tolist()

# Axis range
axis_range = 3.5

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 4800,
    "backgroundColor": "#fafbfc",
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginTop": 180,
    "marginBottom": 200,
    "marginLeft": 280,
    "marginRight": 200,
}

chart.options.title = {
    "text": "scatter-complex-plane · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "600", "color": "#2c3e50", "letterSpacing": "1px"},
    "margin": 50,
}

chart.options.subtitle = {
    "text": "Argand Diagram — 3rd Roots of Unity and Arbitrary Complex Numbers",
    "style": {"fontSize": "38px", "color": "#7f8c8d", "fontWeight": "400"},
}

# X-axis (Real)
chart.options.x_axis = {
    "title": {
        "text": "Real Axis",
        "style": {"fontSize": "44px", "color": "#34495e", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#7f8c8d"}},
    "min": -axis_range,
    "max": axis_range,
    "tickInterval": 1,
    "gridLineWidth": 0,
    "lineColor": "#34495e",
    "lineWidth": 2,
    "tickColor": "#34495e",
    "tickLength": 10,
    "plotLines": [{"value": 0, "color": "#34495e", "width": 3, "zIndex": 1}],
}

# Y-axis (Imaginary)
chart.options.y_axis = {
    "title": {
        "text": "Imaginary Axis",
        "style": {"fontSize": "44px", "color": "#34495e", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#7f8c8d"}},
    "min": -axis_range,
    "max": axis_range,
    "tickInterval": 1,
    "gridLineWidth": 0,
    "lineColor": "#34495e",
    "lineWidth": 2,
    "tickColor": "#34495e",
    "tickLength": 10,
    "plotLines": [{"value": 0, "color": "#34495e", "width": 3, "zIndex": 1}],
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -40,
    "y": 100,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.9)",
    "borderWidth": 1,
    "borderColor": "#e0e0e0",
    "borderRadius": 8,
    "itemStyle": {"fontSize": "34px", "fontWeight": "400", "color": "#34495e"},
    "padding": 20,
    "symbolRadius": 6,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:26px;color:{point.color}">●</span> '
        '<span style="font-size:28px">'
        "{point.name}<br/>"
        "Real: <b>{point.x:.3f}</b> | Imag: <b>{point.y:.3f}</b></span>"
    ),
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 10,
    "borderWidth": 2,
    "style": {"fontSize": "26px"},
}

# Unit circle — dashed reference circle
unit_circle = SplineSeries()
unit_circle.data = [[float(cx), float(cy)] for cx, cy in zip(circle_x, circle_y, strict=True)]
unit_circle.name = "Unit Circle"
unit_circle.color = "#95a5a6"
unit_circle.line_width = 3
unit_circle.dash_style = "Dash"
unit_circle.marker = {"enabled": False}
unit_circle.enable_mouse_tracking = False
unit_circle.z_index = 1
chart.add_series(unit_circle)

# Vector lines from origin to roots of unity
for i in range(n_roots):
    vec = SplineSeries()
    vec.data = [[0.0, 0.0], [float(roots_real[i]), float(roots_imag[i])]]
    vec.color = "rgba(48, 105, 152, 0.5)"
    vec.line_width = 3
    vec.dash_style = "ShortDash"
    vec.marker = {"enabled": False}
    vec.enable_mouse_tracking = False
    vec.show_in_legend = False
    vec.z_index = 2
    chart.add_series(vec)

# Vector lines from origin to arbitrary points
for i in range(len(arb_real)):
    vec = SplineSeries()
    vec.data = [[0.0, 0.0], [float(arb_real[i]), float(arb_imag[i])]]
    vec.color = "rgba(192, 57, 43, 0.4)"
    vec.line_width = 3
    vec.dash_style = "ShortDash"
    vec.marker = {"enabled": False}
    vec.enable_mouse_tracking = False
    vec.show_in_legend = False
    vec.z_index = 2
    chart.add_series(vec)

# Roots of unity scatter series
roots_scatter = ScatterSeries()
roots_scatter.data = [
    {"x": float(roots_real[i]), "y": float(roots_imag[i]), "name": roots_labels[i]} for i in range(n_roots)
]
roots_scatter.name = "3rd Roots of Unity"
roots_scatter.color = "#306998"
roots_scatter.marker = {
    "radius": 18,
    "symbol": "circle",
    "lineWidth": 3,
    "lineColor": "#ffffff",
    "states": {"hover": {"radiusPlus": 5}},
}
roots_scatter.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "style": {"fontSize": "34px", "fontWeight": "600", "color": "#306998", "textOutline": "3px white"},
    "y": -35,
    "allowOverlap": False,
}
roots_scatter.z_index = 5
chart.add_series(roots_scatter)

# Arbitrary complex numbers scatter series
arb_scatter = ScatterSeries()
arb_scatter.data = [
    {"x": float(arb_real[i]), "y": float(arb_imag[i]), "name": arb_labels[i]} for i in range(len(arb_real))
]
arb_scatter.name = "Complex Numbers"
arb_scatter.color = "#c0392b"
arb_scatter.marker = {
    "radius": 16,
    "symbol": "diamond",
    "lineWidth": 3,
    "lineColor": "#ffffff",
    "states": {"hover": {"radiusPlus": 5}},
}
arb_scatter.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "style": {"fontSize": "28px", "fontWeight": "500", "color": "#c0392b", "textOutline": "3px white"},
    "y": -30,
    "allowOverlap": False,
}
arb_scatter.z_index = 5
chart.add_series(arb_scatter)

# Origin marker
origin = ScatterSeries()
origin.data = [{"x": 0.0, "y": 0.0, "name": "Origin"}]
origin.name = "Origin"
origin.color = "#2c3e50"
origin.marker = {"radius": 10, "symbol": "circle", "lineWidth": 2, "lineColor": "#2c3e50", "fillColor": "#2c3e50"}
origin.show_in_legend = False
origin.enable_mouse_tracking = False
origin.z_index = 4
chart.add_series(origin)

# Download Highcharts JS with fallback CDN
highcharts_js = None
cdn_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
for url in cdn_urls:
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
            break
        except urllib.error.HTTPError:
            time.sleep(2 * (attempt + 1))
    if highcharts_js:
        break

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 4800px; height: 4800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,4800")

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
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
