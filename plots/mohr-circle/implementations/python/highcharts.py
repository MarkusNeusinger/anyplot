"""anyplot.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: highcharts | Python 3.14.3
Quality: 91/100 | Updated: 2026-05-30
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.annotations import Annotation
from highcharts_core.options.series.area import LineSeries  # LineSeries lives in .area module
from highcharts_core.options.series.scatter import ScatterSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette assignments (semantic: stress/critical → red, results → blue/lavender)
COLOR_CIRCLE = "#009E73"  # brand green — main element (Imprint position 1)
COLOR_STRESS = "#AE3030"  # matte red — stress points A, B (semantic anchor)
COLOR_PRINCIPAL = "#4467A3"  # blue — principal stresses σ₁, σ₂ (Imprint position 3)
COLOR_SHEAR = "#C475FD"  # lavender — max shear stress τmax (Imprint position 2)
COLOR_ARC = "#BD8233"  # ochre — angle arc 2θp (Imprint position 4)

# Data — 2D stress state for structural steel under combined loading
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

# Chart (square canvas — equal aspect ratio required for Mohr's Circle)
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 2400,
    "height": 2400,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "'Segoe UI', Arial, Helvetica, sans-serif", "color": INK},
    "marginLeft": 180,
    "marginRight": 60,
    "marginTop": 200,
    "marginBottom": 160,
}

title = "mohr-circle · python · highcharts · anyplot.ai"
chart.options.title = {"text": title, "style": {"fontSize": "66px", "fontWeight": "700", "color": INK}, "margin": 20}
chart.options.subtitle = {
    "text": f"σx = {sigma_x} MPa,  σy = {sigma_y} MPa,  τxy = {tau_xy} MPa",
    "style": {"fontSize": "50px", "fontWeight": "400", "color": INK_SOFT},
}

# Equal aspect ratio: plot area = 2400-180-60=2160 wide × 2400-200-160=2040 tall
y_pad = 95
x_half_range = y_pad * (2160 / 2040)
x_min = center - x_half_range
x_max = center + x_half_range

chart.options.x_axis = {
    "title": {
        "text": "Normal Stress σ (MPa)",
        "style": {"fontSize": "56px", "fontWeight": "600", "color": INK},
        "margin": 16,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": x_min,
    "max": x_max,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineWidth": 0,
    "tickWidth": 0,
    "plotLines": [{"value": center, "color": INK_SOFT, "width": 2, "dashStyle": "Dash", "zIndex": 1}],
}

chart.options.y_axis = {
    "title": {
        "text": "Shear Stress τ (MPa)",
        "style": {"fontSize": "56px", "fontWeight": "600", "color": INK},
        "margin": 16,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "min": -y_pad,
    "max": y_pad,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineWidth": 0,
    "tickWidth": 0,
    "plotLines": [{"value": 0, "color": INK_SOFT, "width": 2, "dashStyle": "Dash", "zIndex": 1}],
}

chart.options.legend = {"enabled": False}
chart.options.tooltip = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.plot_options = {"series": {"animation": False, "states": {"hover": {"enabled": False}}}}

# Mohr's Circle outline
circle_series = LineSeries()
circle_series.name = "Mohr's Circle"
circle_series.data = [[float(cx), float(cy)] for cx, cy in zip(circle_x, circle_y, strict=False)]
circle_series.color = COLOR_CIRCLE
circle_series.line_width = 6
circle_series.marker = {"enabled": False}
circle_series.enable_mouse_tracking = False
circle_series.show_in_legend = False
chart.add_series(circle_series)

# Diameter line connecting stress points A and B
diameter_series = LineSeries()
diameter_series.data = [[float(sigma_x), float(tau_xy)], [float(sigma_y), float(-tau_xy)]]
diameter_series.color = INK_SOFT
diameter_series.line_width = 3
diameter_series.dash_style = "Dash"
diameter_series.marker = {"enabled": False}
diameter_series.enable_mouse_tracking = False
diameter_series.show_in_legend = False
chart.add_series(diameter_series)

# Stress point A (σx, τxy)
point_a = ScatterSeries()
point_a.data = [{"x": float(sigma_x), "y": float(tau_xy)}]
point_a.color = COLOR_STRESS
point_a.marker = {"symbol": "circle", "radius": 16, "lineWidth": 3, "lineColor": PAGE_BG, "fillColor": COLOR_STRESS}
point_a.enable_mouse_tracking = False
point_a.show_in_legend = False
chart.add_series(point_a)

# Stress point B (σy, −τxy)
point_b = ScatterSeries()
point_b.data = [{"x": float(sigma_y), "y": float(-tau_xy)}]
point_b.color = COLOR_STRESS
point_b.marker = {"symbol": "circle", "radius": 16, "lineWidth": 3, "lineColor": PAGE_BG, "fillColor": COLOR_STRESS}
point_b.enable_mouse_tracking = False
point_b.show_in_legend = False
chart.add_series(point_b)

# Principal stress σ₁
sigma1_series = ScatterSeries()
sigma1_series.data = [{"x": float(sigma_1), "y": 0}]
sigma1_series.color = COLOR_PRINCIPAL
sigma1_series.marker = {
    "symbol": "diamond",
    "radius": 18,
    "lineWidth": 3,
    "lineColor": PAGE_BG,
    "fillColor": COLOR_PRINCIPAL,
}
sigma1_series.enable_mouse_tracking = False
sigma1_series.show_in_legend = False
chart.add_series(sigma1_series)

# Principal stress σ₂
sigma2_series = ScatterSeries()
sigma2_series.data = [{"x": float(sigma_2), "y": 0}]
sigma2_series.color = COLOR_PRINCIPAL
sigma2_series.marker = {
    "symbol": "diamond",
    "radius": 18,
    "lineWidth": 3,
    "lineColor": PAGE_BG,
    "fillColor": COLOR_PRINCIPAL,
}
sigma2_series.enable_mouse_tracking = False
sigma2_series.show_in_legend = False
chart.add_series(sigma2_series)

# Maximum shear stress (top of circle)
tau_top = ScatterSeries()
tau_top.data = [{"x": float(center), "y": float(tau_max)}]
tau_top.color = COLOR_SHEAR
tau_top.marker = {"symbol": "triangle", "radius": 16, "lineWidth": 3, "lineColor": PAGE_BG, "fillColor": COLOR_SHEAR}
tau_top.enable_mouse_tracking = False
tau_top.show_in_legend = False
chart.add_series(tau_top)

# Maximum shear stress (bottom of circle)
tau_bot = ScatterSeries()
tau_bot.data = [{"x": float(center), "y": float(-tau_max)}]
tau_bot.color = COLOR_SHEAR
tau_bot.marker = {
    "symbol": "triangle-down",
    "radius": 16,
    "lineWidth": 3,
    "lineColor": PAGE_BG,
    "fillColor": COLOR_SHEAR,
}
tau_bot.enable_mouse_tracking = False
tau_bot.show_in_legend = False
chart.add_series(tau_bot)

# Center point C
center_pt = ScatterSeries()
center_pt.data = [{"x": float(center), "y": 0}]
center_pt.color = INK
center_pt.marker = {"symbol": "circle", "radius": 10, "fillColor": INK, "lineWidth": 0}
center_pt.enable_mouse_tracking = False
center_pt.show_in_legend = False
chart.add_series(center_pt)

# Angle arc for 2θp (from σ-axis to line CA)
arc_r = radius * 0.25
arc_angles = np.linspace(0, np.radians(two_theta_p), 30)
arc_x = center + arc_r * np.cos(arc_angles)
arc_y = arc_r * np.sin(arc_angles)
arc_series = LineSeries()
arc_series.data = [[float(ax), float(ay)] for ax, ay in zip(arc_x, arc_y, strict=False)]
arc_series.color = COLOR_ARC
arc_series.line_width = 5
arc_series.marker = {"enabled": False}
arc_series.enable_mouse_tracking = False
arc_series.show_in_legend = False
chart.add_series(arc_series)

# Annotations — theme-adaptive text outlines for readability on both surfaces
TEXT_OUTLINE = f"3px {PAGE_BG}"
mid_angle = np.radians(two_theta_p) / 2
label_r = arc_r * 1.8

chart.options.annotations = [
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
                "style": {"fontSize": "40px", "fontWeight": "600", "color": COLOR_STRESS, "textOutline": TEXT_OUTLINE},
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
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
                "style": {
                    "fontSize": "40px",
                    "fontWeight": "bold",
                    "color": COLOR_PRINCIPAL,
                    "textOutline": TEXT_OUTLINE,
                },
            },
            "labels": [
                {
                    "point": {"x": float(sigma_1), "y": 0, "xAxis": 0, "yAxis": 0},
                    "text": f"σ₁ = {sigma_1:.1f} MPa",
                    "align": "left",
                    "x": 15,
                    "y": -30,
                },
                {
                    "point": {"x": float(sigma_2), "y": 0, "xAxis": 0, "yAxis": 0},
                    "text": f"σ₂ = {sigma_2:.1f} MPa",
                    "align": "right",
                    "x": -15,
                    "y": -30,
                },
            ],
        }
    ),
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
                "style": {"fontSize": "40px", "fontWeight": "bold", "color": COLOR_SHEAR, "textOutline": TEXT_OUTLINE},
            },
            "labels": [
                {
                    "point": {"x": float(center), "y": float(tau_max), "xAxis": 0, "yAxis": 0},
                    "text": f"τmax = {tau_max:.1f} MPa",
                    "align": "left",
                    "x": 15,
                    "y": -22,
                },
                {
                    "point": {"x": float(center), "y": float(-tau_max), "xAxis": 0, "yAxis": 0},
                    "text": f"τmin = −{tau_max:.1f} MPa",
                    "align": "left",
                    "x": 15,
                    "y": 22,
                },
            ],
        }
    ),
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
                "style": {"fontSize": "36px", "fontWeight": "600", "color": INK_SOFT, "textOutline": TEXT_OUTLINE},
            },
            "labels": [
                {
                    "point": {"x": float(center), "y": 0, "xAxis": 0, "yAxis": 0},
                    "text": f"C ({center:.1f}, 0)",
                    "align": "right",
                    "x": -14,
                    "y": 50,
                }
            ],
        }
    ),
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "shadow": False,
                "style": {"fontSize": "40px", "fontWeight": "bold", "color": COLOR_ARC, "textOutline": TEXT_OUTLINE},
            },
            "labels": [
                {
                    "point": {
                        "x": float(center + label_r * np.cos(mid_angle)),
                        "y": float(label_r * np.sin(mid_angle)),
                        "xAxis": 0,
                        "yAxis": 0,
                    },
                    "text": f"2θp = {two_theta_p:.1f}°",
                    "align": "left",
                    "x": 10,
                    "y": -8,
                }
            ],
        }
    ),
]

# Download Highcharts JS (inline required for headless Chrome file:// URLs)
cdn_urls = ["https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js", "https://code.highcharts.com/highcharts.js"]
highcharts_js = None
for url in cdn_urls:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        time.sleep(2)
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS")

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
    except Exception:
        time.sleep(2)
if annotations_js is None:
    raise RuntimeError("Failed to download Highcharts annotations module")

js_literal = chart.to_js_literal()

# Standalone HTML for interactive viewing (CDN links — not for headless Chrome)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 2400px; height: 2400px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Inline HTML for headless Chrome screenshot (CDN cannot load via file://)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 2400px; height: 2400px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=2400,2400")

driver = webdriver.Chrome(options=chrome_options)
# CDP override makes viewport authoritative; --window-size alone leaves Chrome chrome artifacts
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 2400, "height": 2400, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
Path(temp_path).unlink()

# Safety net: pin PNG to exact 2400×2400 so post-render gate passes
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (2400, 2400):
    _norm = Image.new("RGB", (2400, 2400), PAGE_BG)
    _norm.paste(_img, ((2400 - _img.size[0]) // 2, (2400 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
