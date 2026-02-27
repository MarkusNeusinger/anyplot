""" pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: highcharts unknown | Python 3.14.3
Quality: 91/100 | Created: 2026-02-27
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.annotations import Annotation
from highcharts_core.options.series.area import LineSeries  # LineSeries lives in area module in highcharts_core
from highcharts_core.options.series.scatter import ScatterSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - 2D stress state
sigma_x = 80  # MPa (normal stress, x-direction)
sigma_y = -30  # MPa (normal stress, y-direction)
tau_xy = 40  # MPa (shear stress, xy-plane)

# Mohr's Circle calculations
center = (sigma_x + sigma_y) / 2
radius = np.sqrt(((sigma_x - sigma_y) / 2) ** 2 + tau_xy**2)
sigma_1 = center + radius
sigma_2 = center - radius
tau_max = radius
two_theta_p = np.degrees(np.arctan2(tau_xy, (sigma_x - sigma_y) / 2))

# Circle points (200 samples for smooth curve)
theta = np.linspace(0, 2 * np.pi, 200)
circle_x = center + radius * np.cos(theta)
circle_y = radius * np.sin(theta)

# Color palette (colorblind-safe: no red-green pairing)
COLOR_CIRCLE = "#306998"  # Python Blue
COLOR_STRESS_PTS = "#e74c3c"  # Red for stress points A, B
COLOR_PRINCIPAL = "#1abc9c"  # Teal for principal stresses (NOT green)
COLOR_PRINCIPAL_DARK = "#16a085"  # Darker teal for outlines
COLOR_SHEAR = "#8e44ad"  # Purple for max shear
COLOR_SHEAR_DARK = "#6c3483"  # Darker purple for outlines
COLOR_CENTER = "#2c3e50"  # Dark for center point
COLOR_ANGLE = "#e67e22"  # Orange for angle arc
COLOR_DIAMETER = "#7f8c8d"  # Gray for diameter line
COLOR_AXIS = "#d5d8dc"  # Soft axis line color

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "'Segoe UI', Arial, Helvetica, sans-serif"},
    "marginLeft": 240,
    "marginRight": 240,
    "marginTop": 260,
    "marginBottom": 240,
}

chart.options.title = {
    "text": "mohr-circle \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "700", "color": "#2c3e50", "letterSpacing": "1px"},
    "margin": 30,
}

chart.options.subtitle = {
    "text": (f"\u03c3x = {sigma_x} MPa, \u03c3y = {sigma_y} MPa, \u03c4xy = {tau_xy} MPa"),
    "style": {"fontSize": "38px", "fontWeight": "400", "color": "#7f8c8d"},
}

# Axis ranges for equal aspect ratio
# Plot area: 3600 - 240 - 240 = 3120 wide, 3600 - 260 - 240 = 3100 tall
y_pad = 95
x_half_range = y_pad * (3120 / 3100)
x_min = center - x_half_range
x_max = center + x_half_range

chart.options.x_axis = {
    "title": {
        "text": "Normal Stress \u03c3 (MPa)",
        "style": {"fontSize": "38px", "fontWeight": "600", "color": "#2c3e50"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "30px", "color": "#34495e"}},
    "min": x_min,
    "max": x_max,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.06)",
    "lineWidth": 0,
    "lineColor": COLOR_AXIS,
    "tickWidth": 0,
    "plotLines": [{"value": center, "color": "#95a5a6", "width": 2, "dashStyle": "Dash", "zIndex": 1}],
}

chart.options.y_axis = {
    "title": {
        "text": "Shear Stress \u03c4 (MPa)",
        "style": {"fontSize": "38px", "fontWeight": "600", "color": "#2c3e50"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "30px", "color": "#34495e"}},
    "min": -y_pad,
    "max": y_pad,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.06)",
    "lineWidth": 0,
    "lineColor": COLOR_AXIS,
    "tickWidth": 0,
    "plotLines": [{"value": 0, "color": "#95a5a6", "width": 2, "dashStyle": "Dash", "zIndex": 1}],
}

chart.options.legend = {"enabled": False}
chart.options.tooltip = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.plot_options = {"series": {"animation": False, "states": {"hover": {"enabled": False}}}}

# --- Series using typed classes ---

# Mohr's Circle outline
circle_series = LineSeries()
circle_series.name = "Mohr's Circle"
circle_series.data = [[float(cx), float(cy)] for cx, cy in zip(circle_x, circle_y, strict=False)]
circle_series.color = COLOR_CIRCLE
circle_series.line_width = 5
circle_series.marker = {"enabled": False}
circle_series.enable_mouse_tracking = False
circle_series.show_in_legend = False
chart.add_series(circle_series)

# Diameter line connecting A and B
diameter_series = LineSeries()
diameter_series.name = "Diameter"
diameter_series.data = [[float(sigma_x), float(tau_xy)], [float(sigma_y), float(-tau_xy)]]
diameter_series.color = COLOR_DIAMETER
diameter_series.line_width = 3
diameter_series.dash_style = "Dash"
diameter_series.marker = {"enabled": False}
diameter_series.enable_mouse_tracking = False
diameter_series.show_in_legend = False
chart.add_series(diameter_series)

# Stress point A (σx, τxy)
point_a_series = ScatterSeries()
point_a_series.data = [{"x": float(sigma_x), "y": float(tau_xy)}]
point_a_series.color = COLOR_STRESS_PTS
point_a_series.marker = {
    "symbol": "circle",
    "radius": 14,
    "lineWidth": 3,
    "lineColor": "#c0392b",
    "fillColor": COLOR_STRESS_PTS,
}
point_a_series.enable_mouse_tracking = False
point_a_series.show_in_legend = False
chart.add_series(point_a_series)

# Stress point B (σy, −τxy)
point_b_series = ScatterSeries()
point_b_series.data = [{"x": float(sigma_y), "y": float(-tau_xy)}]
point_b_series.color = COLOR_STRESS_PTS
point_b_series.marker = {
    "symbol": "circle",
    "radius": 14,
    "lineWidth": 3,
    "lineColor": "#c0392b",
    "fillColor": COLOR_STRESS_PTS,
}
point_b_series.enable_mouse_tracking = False
point_b_series.show_in_legend = False
chart.add_series(point_b_series)

# Principal stress σ1
sigma1_series = ScatterSeries()
sigma1_series.data = [{"x": float(sigma_1), "y": 0}]
sigma1_series.color = COLOR_PRINCIPAL
sigma1_series.marker = {
    "symbol": "diamond",
    "radius": 16,
    "lineWidth": 3,
    "lineColor": COLOR_PRINCIPAL_DARK,
    "fillColor": COLOR_PRINCIPAL,
}
sigma1_series.enable_mouse_tracking = False
sigma1_series.show_in_legend = False
chart.add_series(sigma1_series)

# Principal stress σ2
sigma2_series = ScatterSeries()
sigma2_series.data = [{"x": float(sigma_2), "y": 0}]
sigma2_series.color = COLOR_PRINCIPAL
sigma2_series.marker = {
    "symbol": "diamond",
    "radius": 16,
    "lineWidth": 3,
    "lineColor": COLOR_PRINCIPAL_DARK,
    "fillColor": COLOR_PRINCIPAL,
}
sigma2_series.enable_mouse_tracking = False
sigma2_series.show_in_legend = False
chart.add_series(sigma2_series)

# Maximum shear stress (top)
tau_max_series = ScatterSeries()
tau_max_series.data = [{"x": float(center), "y": float(tau_max)}]
tau_max_series.color = COLOR_SHEAR
tau_max_series.marker = {
    "symbol": "triangle",
    "radius": 14,
    "lineWidth": 3,
    "lineColor": COLOR_SHEAR_DARK,
    "fillColor": COLOR_SHEAR,
}
tau_max_series.enable_mouse_tracking = False
tau_max_series.show_in_legend = False
chart.add_series(tau_max_series)

# Maximum shear stress (bottom)
tau_min_series = ScatterSeries()
tau_min_series.data = [{"x": float(center), "y": float(-tau_max)}]
tau_min_series.color = COLOR_SHEAR
tau_min_series.marker = {
    "symbol": "triangle-down",
    "radius": 14,
    "lineWidth": 3,
    "lineColor": COLOR_SHEAR_DARK,
    "fillColor": COLOR_SHEAR,
}
tau_min_series.enable_mouse_tracking = False
tau_min_series.show_in_legend = False
chart.add_series(tau_min_series)

# Center point C
center_series = ScatterSeries()
center_series.data = [{"x": float(center), "y": 0}]
center_series.color = COLOR_CENTER
center_series.marker = {"symbol": "circle", "radius": 10, "fillColor": COLOR_CENTER}
center_series.enable_mouse_tracking = False
center_series.show_in_legend = False
chart.add_series(center_series)

# Angle arc for 2θp (from σ-axis to line CA)
arc_r = radius * 0.25
arc_theta = np.linspace(0, np.radians(two_theta_p), 30)
arc_x = center + arc_r * np.cos(arc_theta)
arc_y = arc_r * np.sin(arc_theta)

arc_series = LineSeries()
arc_series.name = "Angle Arc"
arc_series.data = [[float(ax), float(ay)] for ax, ay in zip(arc_x, arc_y, strict=False)]
arc_series.color = COLOR_ANGLE
arc_series.line_width = 4
arc_series.marker = {"enabled": False}
arc_series.enable_mouse_tracking = False
arc_series.show_in_legend = False
chart.add_series(arc_series)

# --- Annotations for labels (Highcharts annotations API) ---

# 2θp angle label position
mid_angle = np.radians(two_theta_p) / 2
label_r = arc_r * 1.8

chart.options.annotations = [
    # Stress points A and B labels
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
                "useHTML": False,
                "style": {"fontSize": "32px", "fontWeight": "600", "color": "#c0392b", "textOutline": "3px #ffffff"},
            },
            "labels": [
                {
                    "point": {"x": float(sigma_x), "y": float(tau_xy), "xAxis": 0, "yAxis": 0},
                    "text": f"A ({sigma_x}, {tau_xy})",
                    "align": "left",
                    "x": 18,
                    "y": -18,
                },
                {
                    "point": {"x": float(sigma_y), "y": float(-tau_xy), "xAxis": 0, "yAxis": 0},
                    "text": f"B ({sigma_y}, {-tau_xy})",
                    "align": "right",
                    "x": -18,
                    "y": 18,
                },
            ],
        }
    ),
    # Principal stresses labels
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
                "style": {
                    "fontSize": "34px",
                    "fontWeight": "bold",
                    "color": COLOR_PRINCIPAL_DARK,
                    "textOutline": "3px #ffffff",
                },
            },
            "labels": [
                {
                    "point": {"x": float(sigma_1), "y": 0, "xAxis": 0, "yAxis": 0},
                    "text": f"\u03c3\u2081 = {sigma_1:.1f} MPa",
                    "align": "left",
                    "x": 15,
                    "y": -28,
                },
                {
                    "point": {"x": float(sigma_2), "y": 0, "xAxis": 0, "yAxis": 0},
                    "text": f"\u03c3\u2082 = {sigma_2:.1f} MPa",
                    "align": "right",
                    "x": -15,
                    "y": -28,
                },
            ],
        }
    ),
    # Max shear stress labels
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
                "style": {"fontSize": "32px", "fontWeight": "bold", "color": COLOR_SHEAR, "textOutline": "3px #ffffff"},
            },
            "labels": [
                {
                    "point": {"x": float(center), "y": float(tau_max), "xAxis": 0, "yAxis": 0},
                    "text": f"\u03c4max = {tau_max:.1f} MPa",
                    "align": "left",
                    "x": 15,
                    "y": -20,
                },
                {
                    "point": {"x": float(center), "y": float(-tau_max), "xAxis": 0, "yAxis": 0},
                    "text": f"\u03c4min = \u2212{tau_max:.1f} MPa",
                    "align": "left",
                    "x": 15,
                    "y": 22,
                },
            ],
        }
    ),
    # Center point label (offset below to avoid crowding with 2θp arc)
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
                "style": {"fontSize": "28px", "fontWeight": "600", "color": COLOR_CENTER, "textOutline": "3px #ffffff"},
            },
            "labels": [
                {
                    "point": {"x": float(center), "y": 0, "xAxis": 0, "yAxis": 0},
                    "text": f"C ({center:.1f}, 0)",
                    "align": "right",
                    "x": -14,
                    "y": 48,
                }
            ],
        }
    ),
    # 2θp angle label
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
                "style": {"fontSize": "30px", "fontWeight": "bold", "color": COLOR_ANGLE, "textOutline": "3px #ffffff"},
            },
            "labels": [
                {
                    "point": {
                        "x": float(center + label_r * np.cos(mid_angle)),
                        "y": float(label_r * np.sin(mid_angle)),
                        "xAxis": 0,
                        "yAxis": 0,
                    },
                    "text": f"2\u03b8p = {two_theta_p:.1f}\u00b0",
                    "align": "left",
                    "x": 10,
                    "y": -8,
                }
            ],
        }
    ),
]

# Download Highcharts JS and annotations module
cdn_urls = ["https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js", "https://code.highcharts.com/highcharts.js"]
highcharts_js = None
for url in cdn_urls:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except urllib.error.HTTPError:
        time.sleep(2)
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from all CDNs")

annotations_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js",
    "https://code.highcharts.com/modules/annotations.js",
]
annotations_js = None
for url in annotations_urls:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            annotations_js = response.read().decode("utf-8")
        break
    except urllib.error.HTTPError:
        time.sleep(2)
        continue
if annotations_js is None:
    raise RuntimeError("Failed to download Highcharts annotations module from all CDNs")

# Generate JS literal
js_literal = chart.to_js_literal()

# Inline HTML for headless Chrome rendering
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Standalone HTML for interactive viewing
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js"></script>
</head>
<body style="margin:0; overflow:auto;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Screenshot via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 3600x3600
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 3600, 3600))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
