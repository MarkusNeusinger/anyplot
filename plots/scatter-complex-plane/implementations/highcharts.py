""" pyplots.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: highcharts unknown | Python 3.14.3
Quality: 89/100 | Created: 2026-03-04
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

# Compute polar form labels for roots (all have r=1)
roots_polar = [f"ω{k} = 1∠{math.degrees(angles_roots[k]):.0f}°" for k in range(n_roots)]

# Arbitrary complex numbers
arb_points = [(2.0, 1.5, "z₁"), (-1.2, 2.0, "z₂"), (1.5, -1.8, "z₃"), (-2.0, -1.0, "z₄"), (0.5, 2.5, "z₅")]
arb_real = [p[0] for p in arb_points]
arb_imag = [p[1] for p in arb_points]

# Compute polar form and rectangular labels for arbitrary points
arb_labels = []
arb_polar = []
for x, y, name in arb_points:
    r = math.sqrt(x**2 + y**2)
    theta_deg = math.degrees(math.atan2(y, x))
    sign = "+" if y >= 0 else "−"
    arb_labels.append(f"{name} = {x:g}{sign}{abs(y):g}i")
    arb_polar.append(f"{r:.2f}∠{theta_deg:.0f}°")

# Complex addition: z₁ + z₂ to demonstrate geometric addition
sum_x = arb_points[0][0] + arb_points[1][0]  # 2.0 + (-1.2) = 0.8
sum_y = arb_points[0][1] + arb_points[1][1]  # 1.5 + 2.0 = 3.5
sum_r = math.sqrt(sum_x**2 + sum_y**2)
sum_theta = math.degrees(math.atan2(sum_y, sum_x))
sum_label = f"z₁+z₂ = {sum_x:g}+{sum_y:g}i"
sum_polar = f"{sum_r:.2f}∠{sum_theta:.0f}°"

# Unit circle points
theta = np.linspace(0, 2 * np.pi, 200)
circle_x = np.cos(theta).tolist()
circle_y = np.sin(theta).tolist()

# Axis range — symmetric, fits sum point at y=3.5 with padding
axis_range = 3.9

# Colors — teal and amber for accessibility (avoids red-green confusion)
COLOR_ROOTS = "#1a7a6d"
COLOR_ARB = "#d4820a"
COLOR_SUM = "#8e44ad"  # Purple for the sum result
COLOR_ROOTS_VEC = "rgba(26, 122, 109, 0.45)"
COLOR_ARB_VEC = "rgba(212, 130, 10, 0.35)"
COLOR_SUM_VEC = "rgba(142, 68, 173, 0.35)"
COLOR_AXIS = "#2c3e50"
COLOR_BG = "#fafbfc"

# Arrowhead geometry
ARROW_SIZE = 0.20
ARROW_SPREAD = math.radians(26)

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
    "marginBottom": 200,
    "marginLeft": 240,
    "marginRight": 160,
}

chart.options.title = {
    "text": "scatter-complex-plane · highcharts · pyplots.ai",
    "style": {"fontSize": "58px", "fontWeight": "600", "color": COLOR_AXIS, "letterSpacing": "1px"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Argand Diagram — Roots of Unity, Complex Addition, and Polar Coordinates",
    "style": {"fontSize": "36px", "color": "#7f8c8d", "fontWeight": "400"},
}

# X-axis (Real) — no outer border, only origin crosshair
chart.options.x_axis = {
    "title": {
        "text": "Real Axis (Re)",
        "style": {"fontSize": "40px", "color": COLOR_AXIS, "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#7f8c8d"}},
    "min": -axis_range,
    "max": axis_range,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(180, 190, 200, 0.20)",
    "gridLineDashStyle": "Dot",
    "lineWidth": 0,
    "tickLength": 0,
    "plotLines": [{"value": 0, "color": COLOR_AXIS, "width": 3, "zIndex": 2}],
}

# Y-axis (Imaginary) — no outer border, only origin crosshair
chart.options.y_axis = {
    "title": {
        "text": "Imaginary Axis (Im)",
        "style": {"fontSize": "40px", "color": COLOR_AXIS, "fontWeight": "500"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "32px", "color": "#7f8c8d"}},
    "min": -axis_range,
    "max": axis_range,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(180, 190, 200, 0.20)",
    "gridLineDashStyle": "Dot",
    "lineWidth": 0,
    "tickLength": 0,
    "plotLines": [{"value": 0, "color": COLOR_AXIS, "width": 3, "zIndex": 2}],
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

# Annotations — use Highcharts annotations API to label the addition operation
chart.options.annotations = [
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": "rgba(255, 255, 255, 0.85)",
            "borderColor": COLOR_SUM,
            "borderRadius": 6,
            "borderWidth": 1,
            "style": {"fontSize": "24px", "color": COLOR_SUM, "fontWeight": "500"},
        },
        "labels": [
            {
                "point": {"x": (arb_real[0] + sum_x) / 2, "y": (arb_imag[0] + sum_y) / 2, "xAxis": 0, "yAxis": 0},
                "text": "z₁ → z₁+z₂",
            },
            {
                "point": {"x": (arb_real[1] + sum_x) / 2, "y": (arb_imag[1] + sum_y) / 2, "xAxis": 0, "yAxis": 0},
                "text": "z₂ → z₁+z₂",
            },
        ],
    }
]

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


# Build all vectors and arrowheads as a consolidated list
def make_vector_series(points_x, points_y, vec_color, arrow_color, line_w):
    """Create vector shaft + arrowhead series for a list of points from origin."""
    series_list = []
    for px, py in zip(points_x, points_y, strict=True):
        angle = math.atan2(py, px)
        # Vector shaft
        vec = SplineSeries()
        vec.data = [[0.0, 0.0], [px, py]]
        vec.color = vec_color
        vec.line_width = line_w
        vec.dash_style = "ShortDash"
        vec.marker = {"enabled": False}
        vec.enable_mouse_tracking = False
        vec.show_in_legend = False
        vec.z_index = 2
        series_list.append(vec)
        # Arrowhead (V-shape)
        arrow = SplineSeries()
        arrow.data = [
            [px - ARROW_SIZE * math.cos(angle - ARROW_SPREAD), py - ARROW_SIZE * math.sin(angle - ARROW_SPREAD)],
            [px, py],
            [px - ARROW_SIZE * math.cos(angle + ARROW_SPREAD), py - ARROW_SIZE * math.sin(angle + ARROW_SPREAD)],
        ]
        arrow.color = arrow_color
        arrow.line_width = line_w
        arrow.marker = {"enabled": False}
        arrow.enable_mouse_tracking = False
        arrow.show_in_legend = False
        arrow.z_index = 3
        series_list.append(arrow)
    return series_list


# Add vectors for roots of unity
for s in make_vector_series(roots_real, roots_imag, COLOR_ROOTS_VEC, COLOR_ROOTS, 4):
    chart.add_series(s)

# Add vectors for arbitrary points
for s in make_vector_series(arb_real, arb_imag, COLOR_ARB_VEC, COLOR_ARB, 3):
    chart.add_series(s)

# Add vector for the sum point
for s in make_vector_series([sum_x], [sum_y], COLOR_SUM_VEC, COLOR_SUM, 3):
    chart.add_series(s)

# Parallelogram construction lines (z₁→sum and z₂→sum) showing vector addition
for px, py in [(arb_real[0], arb_imag[0]), (arb_real[1], arb_imag[1])]:
    pline = SplineSeries()
    pline.data = [[px, py], [sum_x, sum_y]]
    pline.color = "rgba(142, 68, 173, 0.30)"
    pline.line_width = 2
    pline.dash_style = "LongDash"
    pline.marker = {"enabled": False}
    pline.enable_mouse_tracking = False
    pline.show_in_legend = False
    pline.z_index = 1
    chart.add_series(pline)

# Label offsets per root to avoid overlap
root_label_offsets = [
    {"y": -40, "x": 15},  # ω0 at (1, 0) — push right
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

# Label offsets for arbitrary points
arb_label_offsets = [
    {"y": -38, "x": 0},  # z₁ at (2, 1.5) — up
    {"y": -38, "x": 0},  # z₂ at (-1.2, 2) — up
    {"y": 42, "x": 0},  # z₃ at (1.5, -1.8) — down
    {"y": 42, "x": 35},  # z₄ at (-2, -1) — down-right with more offset
    {"y": -38, "x": 0},  # z₅ at (0.5, 2.5) — up
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

# Sum point — z₁ + z₂ showing complex addition
sum_scatter = ScatterSeries()
sum_scatter.data = [{"x": sum_x, "y": sum_y, "name": f"{sum_label}<br/>{sum_polar}", "dataLabels": {"y": -40, "x": 15}}]
sum_scatter.name = "z₁ + z₂ (Addition)"
sum_scatter.color = COLOR_SUM
sum_scatter.marker = {
    "radius": 17,
    "symbol": "triangle",
    "lineWidth": 2,
    "lineColor": "#ffffff",
    "states": {"hover": {"radiusPlus": 5}},
}
sum_scatter.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "useHTML": True,
    "style": {"fontSize": "26px", "fontWeight": "600", "color": COLOR_SUM, "textOutline": "3px white"},
    "allowOverlap": False,
}
sum_scatter.z_index = 5
chart.add_series(sum_scatter)

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

# Download annotations module for parallelogram construction lines
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
