"""anyplot.ai
scatter-complex-plane: Complex Plane Visualization (Argand Diagram)
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-06-02
"""

import math
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint categorical palette — first series always #009E73
COLOR_ROOTS = "#009E73"  # brand green — 3rd roots of unity (first series)
COLOR_ARB = "#C475FD"  # lavender — arbitrary complex numbers (second series)
COLOR_SUM = "#4467A3"  # blue — z₁+z₂ result (third series)
COLOR_ROOTS_VEC = "rgba(0, 158, 115, 0.40)"
COLOR_ARB_VEC = "rgba(196, 117, 253, 0.35)"
COLOR_SUM_VEC = "rgba(68, 103, 163, 0.35)"

# Data — complex numbers for an Argand diagram
# 3rd roots of unity: e^(2πik/3) for k = 0, 1, 2
n_roots = 3
angles_roots = [2 * np.pi * k / n_roots for k in range(n_roots)]
roots_real = [float(np.cos(a)) for a in angles_roots]
roots_imag = [float(np.sin(a)) for a in angles_roots]
roots_polar = [f"ω{k} = 1∠{math.degrees(angles_roots[k]):.0f}°" for k in range(n_roots)]

# Arbitrary complex numbers
arb_points = [(2.0, 1.5, "z₁"), (-1.2, 2.0, "z₂"), (1.5, -1.8, "z₃"), (-2.0, -1.0, "z₄"), (0.5, 2.5, "z₅")]
arb_real = [p[0] for p in arb_points]
arb_imag = [p[1] for p in arb_points]

arb_labels = []
arb_polar_labels = []
for bx, by, bname in arb_points:
    br = math.sqrt(bx**2 + by**2)
    btheta = math.degrees(math.atan2(by, bx))
    sign = "+" if by >= 0 else "−"
    arb_labels.append(f"{bname} = {bx:g}{sign}{abs(by):g}i")
    arb_polar_labels.append(f"{br:.2f}∠{btheta:.0f}°")

# Complex addition: z₁ + z₂ to show geometric addition
sum_x = arb_points[0][0] + arb_points[1][0]  # 0.8
sum_y = arb_points[0][1] + arb_points[1][1]  # 3.5
sum_r = math.sqrt(sum_x**2 + sum_y**2)
sum_theta = math.degrees(math.atan2(sum_y, sum_x))
sum_label = f"z₁+z₂ = {sum_x:g}+{sum_y:g}i"
sum_polar = f"{sum_r:.2f}∠{sum_theta:.0f}°"

# Unit circle points
theta_vals = np.linspace(0, 2 * np.pi, 200)
circle_x = np.cos(theta_vals).tolist()
circle_y = np.sin(theta_vals).tolist()

# Axis range — symmetric, fits sum at y=3.5 with padding
axis_range = 3.7
ARROW_SIZE = 0.20
ARROW_SPREAD = math.radians(26)

# Chart — square canvas 2400×2400 for equal aspect ratio complex plane
chart = Chart(container="container")
chart.options = HighchartsOptions()

title_text = "scatter-complex-plane · python · highcharts · anyplot.ai"
# len=56 < 67-char baseline → no scaling needed; fontSize stays at 66px
chart.options.chart = {
    "type": "scatter",
    "width": 2400,
    "height": 2400,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif", "color": INK},
    "marginTop": 200,
    "marginBottom": 200,
    "marginLeft": 200,
    "marginRight": 200,
}

chart.options.title = {
    "text": title_text,
    "style": {"fontSize": "66px", "fontWeight": "600", "color": INK, "letterSpacing": "1px"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Argand Diagram — Roots of Unity, Complex Addition, and Polar Coordinates",
    "style": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "400"},
}

chart.options.x_axis = {
    "title": {"text": "Real Axis (Re)", "style": {"fontSize": "56px", "color": INK, "fontWeight": "500"}, "margin": 25},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": -axis_range,
    "max": axis_range,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineWidth": 0,
    "tickLength": 0,
    "plotLines": [{"value": 0, "color": INK_SOFT, "width": 4, "zIndex": 2}],
}

chart.options.y_axis = {
    "title": {
        "text": "Imaginary Axis (Im)",
        "style": {"fontSize": "56px", "color": INK, "fontWeight": "500"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": -axis_range,
    "max": axis_range,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineWidth": 0,
    "tickLength": 0,
    "plotLines": [{"value": 0, "color": INK_SOFT, "width": 4, "zIndex": 2}],
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -30,
    "y": 100,
    "floating": True,
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
    "itemStyle": {"fontSize": "40px", "fontWeight": "400", "color": INK},
    "padding": 18,
    "symbolRadius": 6,
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:30px;color:{point.color}">●</span> '
        '<span style="font-size:32px">'
        "{point.name}<br/>"
        "Real: <b>{point.x:.3f}</b> | Imag: <b>{point.y:.3f}</b></span>"
    ),
    "backgroundColor": ELEVATED_BG,
    "borderColor": COLOR_ROOTS,
    "borderRadius": 10,
    "borderWidth": 2,
    "style": {"fontSize": "32px", "color": INK},
}

# Unit circle — dashed reference
unit_circle = SplineSeries()
unit_circle.data = [[float(cx), float(cy)] for cx, cy in zip(circle_x, circle_y, strict=False)]
unit_circle.name = "Unit Circle"
unit_circle.color = INK_MUTED
unit_circle.line_width = 3
unit_circle.dash_style = "Dash"
unit_circle.marker = {"enabled": False}
unit_circle.enable_mouse_tracking = False
unit_circle.z_index = 1
chart.add_series(unit_circle)

# Vectors from origin — roots of unity (green, thicker)
for vx, vy in zip(roots_real, roots_imag, strict=False):
    _angle = math.atan2(vy, vx)
    _vec = SplineSeries()
    _vec.data = [[0.0, 0.0], [vx, vy]]
    _vec.color = COLOR_ROOTS_VEC
    _vec.line_width = 4
    _vec.dash_style = "ShortDash"
    _vec.marker = {"enabled": False}
    _vec.enable_mouse_tracking = False
    _vec.show_in_legend = False
    _vec.z_index = 2
    chart.add_series(_vec)
    _arr = SplineSeries()
    _arr.data = [
        [vx - ARROW_SIZE * math.cos(_angle - ARROW_SPREAD), vy - ARROW_SIZE * math.sin(_angle - ARROW_SPREAD)],
        [vx, vy],
        [vx - ARROW_SIZE * math.cos(_angle + ARROW_SPREAD), vy - ARROW_SIZE * math.sin(_angle + ARROW_SPREAD)],
    ]
    _arr.color = COLOR_ROOTS
    _arr.line_width = 4
    _arr.marker = {"enabled": False}
    _arr.enable_mouse_tracking = False
    _arr.show_in_legend = False
    _arr.z_index = 3
    chart.add_series(_arr)

# Vectors from origin — arbitrary complex numbers (lavender)
for vx, vy in zip(arb_real, arb_imag, strict=False):
    _angle = math.atan2(vy, vx)
    _vec = SplineSeries()
    _vec.data = [[0.0, 0.0], [vx, vy]]
    _vec.color = COLOR_ARB_VEC
    _vec.line_width = 3
    _vec.dash_style = "ShortDash"
    _vec.marker = {"enabled": False}
    _vec.enable_mouse_tracking = False
    _vec.show_in_legend = False
    _vec.z_index = 2
    chart.add_series(_vec)
    _arr = SplineSeries()
    _arr.data = [
        [vx - ARROW_SIZE * math.cos(_angle - ARROW_SPREAD), vy - ARROW_SIZE * math.sin(_angle - ARROW_SPREAD)],
        [vx, vy],
        [vx - ARROW_SIZE * math.cos(_angle + ARROW_SPREAD), vy - ARROW_SIZE * math.sin(_angle + ARROW_SPREAD)],
    ]
    _arr.color = COLOR_ARB
    _arr.line_width = 3
    _arr.marker = {"enabled": False}
    _arr.enable_mouse_tracking = False
    _arr.show_in_legend = False
    _arr.z_index = 3
    chart.add_series(_arr)

# Vector from origin — sum point (blue)
_angle = math.atan2(sum_y, sum_x)
_vec = SplineSeries()
_vec.data = [[0.0, 0.0], [sum_x, sum_y]]
_vec.color = COLOR_SUM_VEC
_vec.line_width = 3
_vec.dash_style = "ShortDash"
_vec.marker = {"enabled": False}
_vec.enable_mouse_tracking = False
_vec.show_in_legend = False
_vec.z_index = 2
chart.add_series(_vec)
_arr = SplineSeries()
_arr.data = [
    [sum_x - ARROW_SIZE * math.cos(_angle - ARROW_SPREAD), sum_y - ARROW_SIZE * math.sin(_angle - ARROW_SPREAD)],
    [sum_x, sum_y],
    [sum_x - ARROW_SIZE * math.cos(_angle + ARROW_SPREAD), sum_y - ARROW_SIZE * math.sin(_angle + ARROW_SPREAD)],
]
_arr.color = COLOR_SUM
_arr.line_width = 3
_arr.marker = {"enabled": False}
_arr.enable_mouse_tracking = False
_arr.show_in_legend = False
_arr.z_index = 3
chart.add_series(_arr)

# Parallelogram construction lines z₁→sum and z₂→sum
for px, py in [(arb_real[0], arb_imag[0]), (arb_real[1], arb_imag[1])]:
    _pline = SplineSeries()
    _pline.data = [[px, py], [sum_x, sum_y]]
    _pline.color = "rgba(68, 103, 163, 0.30)"
    _pline.line_width = 2
    _pline.dash_style = "LongDash"
    _pline.marker = {"enabled": False}
    _pline.enable_mouse_tracking = False
    _pline.show_in_legend = False
    _pline.z_index = 1
    chart.add_series(_pline)

# Roots of unity scatter — large circles, green
root_label_offsets = [
    {"y": -44, "x": 18},  # ω0 at (1, 0) — push right
    {"y": -50, "x": -10},  # ω1 at (-0.5, 0.87) — push up
    {"y": 52, "x": -10},  # ω2 at (-0.5, -0.87) — push down
]
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
    "radius": 24,
    "symbol": "circle",
    "lineWidth": 3,
    "lineColor": PAGE_BG,
    "states": {"hover": {"radiusPlus": 5}},
}
roots_scatter.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "style": {"fontSize": "28px", "fontWeight": "700", "color": COLOR_ROOTS, "textOutline": f"4px {PAGE_BG}"},
    "allowOverlap": False,
}
roots_scatter.z_index = 5
chart.add_series(roots_scatter)

# Arbitrary complex numbers scatter — diamonds, lavender
arb_label_offsets = [
    {"y": -48, "x": 0},  # z₁ at (2, 1.5) — up
    {"y": -70, "x": -20},  # z₂ at (-1.2, 2) — up-left, further from sum/z₅
    {"y": 54, "x": 0},  # z₃ at (1.5, -1.8) — down
    {"y": 54, "x": 60},  # z₄ at (-2, -1) — down-right, avoid edge
    {"y": 68, "x": 0},  # z₅ at (0.5, 2.5) — down, away from sum above
]
arb_scatter = ScatterSeries()
arb_scatter.data = [
    {
        "x": arb_real[i],
        "y": arb_imag[i],
        "name": f"{arb_labels[i]}<br/>{arb_polar_labels[i]}",
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
    "lineColor": PAGE_BG,
    "states": {"hover": {"radiusPlus": 5}},
}
arb_scatter.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "useHTML": True,
    "style": {"fontSize": "28px", "fontWeight": "500", "color": COLOR_ARB, "textOutline": f"3px {PAGE_BG}"},
    "allowOverlap": False,
}
arb_scatter.z_index = 5
chart.add_series(arb_scatter)

# Sum point scatter — triangle, blue
sum_scatter = ScatterSeries()
sum_scatter.data = [{"x": sum_x, "y": sum_y, "name": f"{sum_label}<br/>{sum_polar}", "dataLabels": {"y": -64, "x": 0}}]
sum_scatter.name = "z₁ + z₂ (Addition)"
sum_scatter.color = COLOR_SUM
sum_scatter.marker = {
    "radius": 17,
    "symbol": "triangle",
    "lineWidth": 2,
    "lineColor": PAGE_BG,
    "states": {"hover": {"radiusPlus": 5}},
}
sum_scatter.data_labels = {
    "enabled": True,
    "format": "{point.name}",
    "useHTML": True,
    "style": {"fontSize": "28px", "fontWeight": "600", "color": COLOR_SUM, "textOutline": f"3px {PAGE_BG}"},
    "allowOverlap": False,
}
sum_scatter.z_index = 5
chart.add_series(sum_scatter)

# Origin marker
origin = ScatterSeries()
origin.data = [{"x": 0.0, "y": 0.0, "name": "O (Origin)"}]
origin.name = "Origin"
origin.color = INK
origin.marker = {"radius": 9, "symbol": "circle", "lineWidth": 2, "lineColor": INK, "fillColor": INK}
origin.data_labels = {
    "enabled": True,
    "format": "O",
    "style": {"fontSize": "36px", "fontWeight": "600", "color": INK, "textOutline": f"3px {PAGE_BG}"},
    "x": 20,
    "y": 28,
    "allowOverlap": False,
}
origin.show_in_legend = False
origin.enable_mouse_tracking = False
origin.z_index = 4
chart.add_series(origin)

# Download Highcharts JS inline (headless Chrome cannot load external CDN from file://)
highcharts_js = None
cdn_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
for _url in cdn_urls:
    for _attempt in range(3):
        try:
            _req = urllib.request.Request(_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(_req, timeout=30) as _resp:
                highcharts_js = _resp.read().decode("utf-8")
            break
        except Exception:
            time.sleep(2 * (_attempt + 1))
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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 2400px; height: 2400px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as _f:
    _f.write(html_content)

# Screenshot via headless Chrome with authoritative CDP viewport override
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as _f:
    _f.write(html_content)
    temp_path = _f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=2400,2400")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone is eaten by Chrome chrome (~139px)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 2400, "height": 2400, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Belt-and-braces: pin PNG to exact 2400×2400 so post-render gate passes
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (2400, 2400):
    _norm = Image.new("RGB", (2400, 2400), PAGE_BG)
    _norm.paste(_img, ((2400 - _img.size[0]) // 2, (2400 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
