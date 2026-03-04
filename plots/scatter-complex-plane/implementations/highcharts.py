""" pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: highcharts unknown | Python 3.14.3
Quality: 86/100 | Created: 2026-03-04
"""

import math
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
roots_real = [float(np.cos(a)) for a in angles_roots]
roots_imag = [float(np.sin(a)) for a in angles_roots]
roots_labels = [f"ω{k}" for k in range(n_roots)]

# Compute polar form for roots (all have r=1)
roots_polar = []
for k in range(n_roots):
    r = 1.0
    theta_deg = math.degrees(angles_roots[k])
    roots_polar.append(f"ω{k} = 1∠{theta_deg:.0f}°")

# Arbitrary complex numbers
arb_points = [(2.0, 1.5, "z₁"), (-1.2, 2.0, "z₂"), (1.5, -1.8, "z₃"), (-2.0, -1.0, "z₄"), (0.5, 2.5, "z₅")]
arb_real = [p[0] for p in arb_points]
arb_imag = [p[1] for p in arb_points]
arb_short = [p[2] for p in arb_points]

# Compute polar form and full labels for arbitrary points
arb_labels = []
arb_polar = []
for x, y, name in arb_points:
    r = math.sqrt(x**2 + y**2)
    theta_deg = math.degrees(math.atan2(y, x))
    sign = "+" if y >= 0 else "−"
    arb_labels.append(f"{name} = {x:g}{sign}{abs(y):g}i")
    arb_polar.append(f"{r:.2f}∠{theta_deg:.0f}°")

# Sum of roots of unity (should be ~0)
sum_real = sum(roots_real)
sum_imag = sum(roots_imag)

# Unit circle points
theta = np.linspace(0, 2 * np.pi, 200)
circle_x = np.cos(theta).tolist()
circle_y = np.sin(theta).tolist()

# Axis range
axis_range = 3.5

# Colors — teal and amber for better accessibility (avoids blue-red confusion)
COLOR_ROOTS = "#1a7a6d"  # Teal for roots of unity
COLOR_ARB = "#d4820a"  # Amber for arbitrary points
COLOR_ROOTS_VEC = "rgba(26, 122, 109, 0.45)"
COLOR_ARB_VEC = "rgba(212, 130, 10, 0.35)"
COLOR_AXIS = "#2c3e50"
COLOR_BG = "#fafbfc"


# Arrowhead geometry parameters
ARROW_SIZE = 0.18
ARROW_SPREAD = math.radians(28)
ARROW_SIZE_SMALL = 0.15

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "scatter",
    "width": 3600,
    "height": 3600,
    "backgroundColor": COLOR_BG,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginTop": 160,
    "marginBottom": 320,
    "marginLeft": 260,
    "marginRight": 180,
}

chart.options.title = {
    "text": "scatter-complex-plane · highcharts · pyplots.ai",
    "style": {"fontSize": "58px", "fontWeight": "600", "color": COLOR_AXIS, "letterSpacing": "1px"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Argand Diagram — 3rd Roots of Unity and Arbitrary Complex Numbers",
    "style": {"fontSize": "36px", "color": "#7f8c8d", "fontWeight": "400"},
}

# X-axis (Real)
chart.options.x_axis = {
    "title": {
        "text": "Real Axis (Re)",
        "style": {"fontSize": "40px", "color": COLOR_AXIS, "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#7f8c8d"}},
    "min": -axis_range,
    "max": axis_range,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(180, 190, 200, 0.25)",
    "gridLineDashStyle": "Dot",
    "lineColor": COLOR_AXIS,
    "lineWidth": 2,
    "tickColor": COLOR_AXIS,
    "tickLength": 10,
    "plotLines": [{"value": 0, "color": COLOR_AXIS, "width": 3, "zIndex": 1}],
}

# Y-axis (Imaginary)
chart.options.y_axis = {
    "title": {
        "text": "Imaginary Axis (Im)",
        "style": {"fontSize": "40px", "color": COLOR_AXIS, "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#7f8c8d"}},
    "min": -axis_range,
    "max": axis_range,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(180, 190, 200, 0.25)",
    "gridLineDashStyle": "Dot",
    "lineColor": COLOR_AXIS,
    "lineWidth": 2,
    "tickColor": COLOR_AXIS,
    "tickLength": 10,
    "plotLines": [{"value": 0, "color": COLOR_AXIS, "width": 3, "zIndex": 1}],
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -30,
    "y": 80,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.92)",
    "borderWidth": 1,
    "borderColor": "#d0d0d0",
    "borderRadius": 8,
    "itemStyle": {"fontSize": "30px", "fontWeight": "400", "color": COLOR_AXIS},
    "padding": 18,
    "symbolRadius": 6,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:24px;color:{point.color}">●</span> '
        '<span style="font-size:26px">'
        "{point.name}<br/>"
        "Real: <b>{point.x:.3f}</b> | Imag: <b>{point.y:.3f}</b></span>"
    ),
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": COLOR_ROOTS,
    "borderRadius": 10,
    "borderWidth": 2,
    "style": {"fontSize": "24px"},
}

# Unit circle — dashed reference circle
unit_circle = SplineSeries()
unit_circle.data = [[float(cx), float(cy)] for cx, cy in zip(circle_x, circle_y, strict=True)]
unit_circle.name = "Unit Circle"
unit_circle.color = "#b0b8bf"
unit_circle.line_width = 3
unit_circle.dash_style = "Dash"
unit_circle.marker = {"enabled": False}
unit_circle.enable_mouse_tracking = False
unit_circle.z_index = 1
chart.add_series(unit_circle)

# Vector lines from origin to roots of unity (with arrowheads)
for i in range(n_roots):
    rx, ry = roots_real[i], roots_imag[i]
    # Vector shaft
    vec = SplineSeries()
    vec.data = [[0.0, 0.0], [rx, ry]]
    vec.color = COLOR_ROOTS_VEC
    vec.line_width = 4
    vec.dash_style = "ShortDash"
    vec.marker = {"enabled": False}
    vec.enable_mouse_tracking = False
    vec.show_in_legend = False
    vec.z_index = 2
    chart.add_series(vec)
    # Arrowhead (V-shape) — inlined geometry
    angle = math.atan2(ry, rx)
    arrow = SplineSeries()
    arrow.data = [
        [
            rx - ARROW_SIZE_SMALL * math.cos(angle - ARROW_SPREAD),
            ry - ARROW_SIZE_SMALL * math.sin(angle - ARROW_SPREAD),
        ],
        [rx, ry],
        [
            rx - ARROW_SIZE_SMALL * math.cos(angle + ARROW_SPREAD),
            ry - ARROW_SIZE_SMALL * math.sin(angle + ARROW_SPREAD),
        ],
    ]
    arrow.color = COLOR_ROOTS
    arrow.line_width = 4
    arrow.marker = {"enabled": False}
    arrow.enable_mouse_tracking = False
    arrow.show_in_legend = False
    arrow.z_index = 3
    chart.add_series(arrow)

# Vector lines from origin to arbitrary points (with arrowheads)
for i in range(len(arb_real)):
    ax, ay = arb_real[i], arb_imag[i]
    # Vector shaft
    vec = SplineSeries()
    vec.data = [[0.0, 0.0], [ax, ay]]
    vec.color = COLOR_ARB_VEC
    vec.line_width = 3
    vec.dash_style = "ShortDash"
    vec.marker = {"enabled": False}
    vec.enable_mouse_tracking = False
    vec.show_in_legend = False
    vec.z_index = 2
    chart.add_series(vec)
    # Arrowhead (V-shape) — inlined geometry
    angle = math.atan2(ay, ax)
    arrow = SplineSeries()
    arrow.data = [
        [ax - ARROW_SIZE * math.cos(angle - ARROW_SPREAD), ay - ARROW_SIZE * math.sin(angle - ARROW_SPREAD)],
        [ax, ay],
        [ax - ARROW_SIZE * math.cos(angle + ARROW_SPREAD), ay - ARROW_SIZE * math.sin(angle + ARROW_SPREAD)],
    ]
    arrow.color = COLOR_ARB
    arrow.line_width = 3
    arrow.marker = {"enabled": False}
    arrow.enable_mouse_tracking = False
    arrow.show_in_legend = False
    arrow.z_index = 3
    chart.add_series(arrow)

# Label offsets per root to avoid overlap (custom y-offsets)
root_label_offsets = [
    {"y": -40, "x": 15},  # ω0 at (1, 0) — push up-right
    {"y": -40, "x": -10},  # ω1 at (-0.5, 0.87) — push up
    {"y": 45, "x": -10},  # ω2 at (-0.5, -0.87) — push down
]

# Roots of unity scatter series — focal points with larger markers
roots_scatter = ScatterSeries()
roots_scatter.data = [
    {
        "x": roots_real[i],
        "y": roots_imag[i],
        "name": roots_polar[i],
        "dataLabels": {"y": root_label_offsets[i]["y"], "x": root_label_offsets[i]["x"]},
    }
    for i in range(n_roots)
]
roots_scatter.name = "3rd Roots of Unity"
roots_scatter.color = COLOR_ROOTS
roots_scatter.marker = {
    "radius": 20,
    "symbol": "circle",
    "lineWidth": 3,
    "lineColor": "#ffffff",
    "states": {"hover": {"radiusPlus": 5}},
}
roots_scatter.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "style": {"fontSize": "30px", "fontWeight": "700", "color": COLOR_ROOTS, "textOutline": "4px white"},
    "allowOverlap": False,
}
roots_scatter.z_index = 5
chart.add_series(roots_scatter)

# Label offsets per arbitrary point to avoid overlap
arb_label_offsets = [
    {"y": -35, "x": 0},  # z₁ at (2, 1.5) — up
    {"y": -35, "x": 0},  # z₂ at (-1.2, 2) — up
    {"y": 40, "x": 0},  # z₃ at (1.5, -1.8) — down
    {"y": 40, "x": 25},  # z₄ at (-2, -1) — down-right to avoid left edge
    {"y": -35, "x": 0},  # z₅ at (0.5, 2.5) — up
]

# Arbitrary complex numbers scatter series
arb_scatter = ScatterSeries()
arb_scatter.data = [
    {
        "x": arb_real[i],
        "y": arb_imag[i],
        "name": f"{arb_labels[i]}<br/>{arb_polar[i]}",
        "dataLabels": {"y": arb_label_offsets[i]["y"], "x": arb_label_offsets[i]["x"]},
    }
    for i in range(len(arb_real))
]
arb_scatter.name = "Complex Numbers"
arb_scatter.color = COLOR_ARB
arb_scatter.marker = {
    "radius": 15,
    "symbol": "diamond",
    "lineWidth": 2,
    "lineColor": "#ffffff",
    "states": {"hover": {"radiusPlus": 5}},
}
arb_scatter.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "useHTML": True,
    "style": {"fontSize": "26px", "fontWeight": "500", "color": COLOR_ARB, "textOutline": "3px white"},
    "allowOverlap": False,
}
arb_scatter.z_index = 5
chart.add_series(arb_scatter)

# Origin marker
origin = ScatterSeries()
origin.data = [{"x": 0.0, "y": 0.0, "name": "O (Origin)"}]
origin.name = "Origin"
origin.color = COLOR_AXIS
origin.marker = {"radius": 9, "symbol": "circle", "lineWidth": 2, "lineColor": COLOR_AXIS, "fillColor": COLOR_AXIS}
origin.data_labels = {
    "enabled": True,
    "format": "O",
    "style": {"fontSize": "28px", "fontWeight": "600", "color": COLOR_AXIS, "textOutline": "3px white"},
    "x": 20,
    "y": 25,
    "allowOverlap": False,
}
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

# Also download annotations module for richer annotation features
annotations_js = ""
ann_url = "https://code.highcharts.com/modules/annotations.js"
try:
    req = urllib.request.Request(ann_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        annotations_js = response.read().decode("utf-8")
except Exception:
    pass

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:{COLOR_BG};">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
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
chrome_options.add_argument("--window-size=3600,3600")

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
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0; background:{COLOR_BG};">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
