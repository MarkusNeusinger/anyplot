""" pyplots.ai
mohr-circle: Mohr's Circle for Stress Analysis
Library: highcharts unknown | Python 3.14.3
Quality: 85/100 | Created: 2026-02-27
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
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

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "'Segoe UI', Arial, Helvetica, sans-serif"},
    "marginLeft": 280,
    "marginRight": 280,
    "marginTop": 200,
    "marginBottom": 220,
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
# Plot area: 4800 - 280 - 280 = 4240 wide, 2700 - 200 - 220 = 2280 tall
y_pad = 95
x_half_range = y_pad * (4240 / 2280)
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
    "lineWidth": 2,
    "lineColor": "#bdc3c7",
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
    "lineWidth": 2,
    "lineColor": "#bdc3c7",
    "tickWidth": 0,
    "plotLines": [{"value": 0, "color": "#95a5a6", "width": 2, "dashStyle": "Dash", "zIndex": 1}],
}

chart.options.legend = {"enabled": False}
chart.options.tooltip = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.plot_options = {"series": {"animation": False, "states": {"hover": {"enabled": False}}}}

# Mohr's Circle outline
circle_data = [[float(cx), float(cy)] for cx, cy in zip(circle_x, circle_y, strict=False)]
chart.add_series(
    {
        "type": "line",
        "name": "Mohr's Circle",
        "data": circle_data,
        "color": "#306998",
        "lineWidth": 5,
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Diameter line connecting A and B
chart.add_series(
    {
        "type": "line",
        "name": "Diameter",
        "data": [[float(sigma_x), float(tau_xy)], [float(sigma_y), float(-tau_xy)]],
        "color": "#7f8c8d",
        "lineWidth": 3,
        "dashStyle": "Dash",
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Stress point A (σx, τxy)
chart.add_series(
    {
        "type": "scatter",
        "data": [
            {
                "x": float(sigma_x),
                "y": float(tau_xy),
                "dataLabels": {
                    "enabled": True,
                    "format": f"A ({sigma_x}, {tau_xy})",
                    "align": "left",
                    "x": 18,
                    "y": -12,
                    "style": {
                        "fontSize": "32px",
                        "fontWeight": "600",
                        "color": "#c0392b",
                        "textOutline": "3px #ffffff",
                    },
                },
            }
        ],
        "color": "#e74c3c",
        "marker": {"symbol": "circle", "radius": 14, "lineWidth": 3, "lineColor": "#c0392b", "fillColor": "#e74c3c"},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Stress point B (σy, −τxy)
chart.add_series(
    {
        "type": "scatter",
        "data": [
            {
                "x": float(sigma_y),
                "y": float(-tau_xy),
                "dataLabels": {
                    "enabled": True,
                    "format": f"B ({sigma_y}, {-tau_xy})",
                    "align": "right",
                    "x": -18,
                    "y": 12,
                    "style": {
                        "fontSize": "32px",
                        "fontWeight": "600",
                        "color": "#c0392b",
                        "textOutline": "3px #ffffff",
                    },
                },
            }
        ],
        "color": "#e74c3c",
        "marker": {"symbol": "circle", "radius": 14, "lineWidth": 3, "lineColor": "#c0392b", "fillColor": "#e74c3c"},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Principal stress σ1
chart.add_series(
    {
        "type": "scatter",
        "data": [
            {
                "x": float(sigma_1),
                "y": 0,
                "dataLabels": {
                    "enabled": True,
                    "format": f"\u03c3\u2081 = {sigma_1:.1f} MPa",
                    "align": "left",
                    "x": 15,
                    "y": -22,
                    "style": {
                        "fontSize": "34px",
                        "fontWeight": "bold",
                        "color": "#27ae60",
                        "textOutline": "3px #ffffff",
                    },
                },
            }
        ],
        "color": "#27ae60",
        "marker": {"symbol": "diamond", "radius": 16, "lineWidth": 3, "lineColor": "#1e8449", "fillColor": "#27ae60"},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Principal stress σ2
chart.add_series(
    {
        "type": "scatter",
        "data": [
            {
                "x": float(sigma_2),
                "y": 0,
                "dataLabels": {
                    "enabled": True,
                    "format": f"\u03c3\u2082 = {sigma_2:.1f} MPa",
                    "align": "right",
                    "x": -15,
                    "y": -22,
                    "style": {
                        "fontSize": "34px",
                        "fontWeight": "bold",
                        "color": "#27ae60",
                        "textOutline": "3px #ffffff",
                    },
                },
            }
        ],
        "color": "#27ae60",
        "marker": {"symbol": "diamond", "radius": 16, "lineWidth": 3, "lineColor": "#1e8449", "fillColor": "#27ae60"},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Maximum shear stress (top)
chart.add_series(
    {
        "type": "scatter",
        "data": [
            {
                "x": float(center),
                "y": float(tau_max),
                "dataLabels": {
                    "enabled": True,
                    "format": f"\u03c4max = {tau_max:.1f} MPa",
                    "align": "left",
                    "x": 15,
                    "y": -15,
                    "style": {
                        "fontSize": "32px",
                        "fontWeight": "bold",
                        "color": "#8e44ad",
                        "textOutline": "3px #ffffff",
                    },
                },
            }
        ],
        "color": "#8e44ad",
        "marker": {"symbol": "triangle", "radius": 14, "lineWidth": 3, "lineColor": "#6c3483", "fillColor": "#8e44ad"},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Maximum shear stress (bottom)
chart.add_series(
    {
        "type": "scatter",
        "data": [
            {
                "x": float(center),
                "y": float(-tau_max),
                "dataLabels": {
                    "enabled": True,
                    "format": f"\u03c4min = \u2212{tau_max:.1f} MPa",
                    "align": "left",
                    "x": 15,
                    "y": 18,
                    "style": {
                        "fontSize": "32px",
                        "fontWeight": "bold",
                        "color": "#8e44ad",
                        "textOutline": "3px #ffffff",
                    },
                },
            }
        ],
        "color": "#8e44ad",
        "marker": {
            "symbol": "triangle-down",
            "radius": 14,
            "lineWidth": 3,
            "lineColor": "#6c3483",
            "fillColor": "#8e44ad",
        },
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Center point C
chart.add_series(
    {
        "type": "scatter",
        "data": [
            {
                "x": float(center),
                "y": 0,
                "dataLabels": {
                    "enabled": True,
                    "format": f"C ({center:.1f}, 0)",
                    "align": "center",
                    "y": 32,
                    "style": {
                        "fontSize": "28px",
                        "fontWeight": "600",
                        "color": "#2c3e50",
                        "textOutline": "3px #ffffff",
                    },
                },
            }
        ],
        "color": "#2c3e50",
        "marker": {"symbol": "circle", "radius": 10, "fillColor": "#2c3e50"},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Angle arc for 2θp (from σ-axis to line CA)
arc_r = radius * 0.25
arc_theta = np.linspace(0, np.radians(two_theta_p), 30)
arc_x = center + arc_r * np.cos(arc_theta)
arc_y = arc_r * np.sin(arc_theta)
arc_data = [[float(ax), float(ay)] for ax, ay in zip(arc_x, arc_y, strict=False)]

chart.add_series(
    {
        "type": "line",
        "data": arc_data,
        "color": "#e67e22",
        "lineWidth": 4,
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# 2θp angle label
mid_angle = np.radians(two_theta_p) / 2
label_r = arc_r * 1.5
chart.add_series(
    {
        "type": "scatter",
        "data": [
            {
                "x": float(center + label_r * np.cos(mid_angle)),
                "y": float(label_r * np.sin(mid_angle)),
                "dataLabels": {
                    "enabled": True,
                    "format": f"2\u03b8p = {two_theta_p:.1f}\u00b0",
                    "align": "left",
                    "x": 10,
                    "y": -5,
                    "style": {
                        "fontSize": "30px",
                        "fontWeight": "bold",
                        "color": "#e67e22",
                        "textOutline": "3px #ffffff",
                    },
                },
            }
        ],
        "marker": {"enabled": False},
        "enableMouseTracking": False,
        "showInLegend": False,
    }
)

# Download Highcharts JS
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

# Generate JS literal
js_literal = chart.to_js_literal()

# Inline HTML for headless Chrome rendering
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Standalone HTML for interactive viewing
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"></script>
</head>
<body style="margin:0; overflow:auto;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
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
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
