""" pyplots.ai
lightcurve-transit: Astronomical Light Curve
Library: highcharts unknown | Python 3.14.3
Quality: 90/100 | Created: 2026-03-18
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.annotations import Annotation
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Simulated exoplanet transit (phase-folded)
np.random.seed(42)

n_points = 400
phase = np.sort(np.random.uniform(0.0, 1.0, n_points))

# Transit model parameters
transit_center = 0.5
transit_depth = 0.01
half_duration = 0.04
ingress_width = 0.012

# Compute transit model inline (KISS: no function definitions)
dist = np.abs(phase - transit_center)
ingress = 0.5 * (1.0 + np.tanh((half_duration - dist) / ingress_width))
limb = np.clip(1.0 - 0.15 * (dist / half_duration) ** 2, 0.85, 1.0)
model_flux = 1.0 - transit_depth * ingress * limb

# Observed flux with noise
flux_err = np.random.uniform(0.001, 0.003, n_points)
flux = model_flux + np.random.normal(0, 1, n_points) * flux_err

# Model curve (smooth, denser sampling for spline)
model_phase = np.linspace(0.0, 1.0, 500)
dist_m = np.abs(model_phase - transit_center)
ingress_m = 0.5 * (1.0 + np.tanh((half_duration - dist_m) / ingress_width))
limb_m = np.clip(1.0 - 0.15 * (dist_m / half_duration) ** 2, 0.85, 1.0)
model_curve = 1.0 - transit_depth * ingress_m * limb_m

# Transit depth for annotation
min_model_flux = float(np.min(model_curve))
depth_ppm = (1.0 - min_model_flux) * 1e6

# Create chart with typed API
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginTop": 160,
    "marginBottom": 300,
    "marginLeft": 280,
    "marginRight": 160,
}

# Title
chart.options.title = {
    "text": "lightcurve-transit \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "600", "color": "#2c3e50", "letterSpacing": "1px"},
    "margin": 50,
}

# Subtitle
chart.options.subtitle = {
    "text": "Phase-folded exoplanet transit with quadratic limb darkening model",
    "style": {"fontSize": "38px", "color": "#7f8c8d", "fontWeight": "400"},
}

# X-axis with crosshair and refined styling
chart.options.x_axis = {
    "title": {
        "text": "Orbital Phase",
        "style": {"fontSize": "44px", "color": "#34495e", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#7f8c8d"}},
    "min": 0.0,
    "max": 1.0,
    "tickInterval": 0.1,
    "gridLineWidth": 0,
    "lineColor": "#bdc3c7",
    "lineWidth": 2,
    "tickColor": "#bdc3c7",
    "tickLength": 10,
    "crosshair": {"width": 2, "color": "rgba(48, 105, 152, 0.25)", "dashStyle": "Dash"},
    "plotBands": [
        {
            "from": transit_center - half_duration * 1.5,
            "to": transit_center + half_duration * 1.5,
            "color": "rgba(212, 81, 61, 0.04)",
            "label": {
                "text": "Transit Window",
                "style": {"fontSize": "30px", "color": "rgba(212, 81, 61, 0.6)", "fontWeight": "500"},
                "align": "center",
                "verticalAlign": "bottom",
                "y": -10,
            },
        }
    ],
}

# Y-axis — no opposite spine (only left + bottom axes visible)
chart.options.y_axis = {
    "title": {
        "text": "Relative Flux",
        "style": {"fontSize": "44px", "color": "#34495e", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#7f8c8d"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#bdc3c7",
    "lineWidth": 2,
    "tickColor": "#bdc3c7",
    "tickLength": 10,
    "crosshair": {"width": 1, "color": "rgba(48, 105, 152, 0.2)", "dashStyle": "Dot"},
    "plotLines": [
        {
            "value": 1.0,
            "color": "rgba(48, 105, 152, 0.3)",
            "width": 2,
            "dashStyle": "LongDash",
            "label": {
                "text": "Baseline flux = 1.0",
                "align": "right",
                "x": -20,
                "y": -14,
                "style": {"fontSize": "28px", "color": "rgba(48, 105, 152, 0.5)"},
            },
            "zIndex": 1,
        }
    ],
}

# Legend with background
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
    "itemStyle": {"fontSize": "32px", "fontWeight": "400", "color": "#34495e"},
    "padding": 16,
    "symbolRadius": 6,
    "itemMarginBottom": 10,
}

chart.options.credits = {"enabled": False}

# Rich tooltip — distinctive Highcharts feature
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:24px;color:{point.color}">\u25cf</span> '
        '<span style="font-size:26px">'
        "Phase: <b>{point.x:.4f}</b><br/>"
        "Flux: <b>{point.y:.6f}</b></span>"
    ),
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 10,
    "borderWidth": 2,
    "shadow": {"color": "rgba(0,0,0,0.1)", "offsetX": 2, "offsetY": 2, "width": 4},
    "style": {"fontSize": "26px"},
}

# Error band using AreaRangeSeries — distinctive Highcharts feature
error_band = AreaRangeSeries()
error_band.data = [
    [round(float(p), 5), round(float(f - e), 6), round(float(f + e), 6)]
    for p, f, e in zip(phase, flux, flux_err, strict=True)
]
error_band.name = "Measurement Error"
error_band.color = "rgba(48, 105, 152, 0.15)"
error_band.fill_opacity = 0.2
error_band.line_width = 0
error_band.marker = {"enabled": False}
error_band.z_index = 0
error_band.enable_mouse_tracking = False

# Scatter series — observed flux with larger markers
scatter = ScatterSeries()
scatter.data = [[round(float(p), 5), round(float(f), 6)] for p, f in zip(phase, flux, strict=True)]
scatter.name = "Observed Flux"
scatter.color = "rgba(48, 105, 152, 0.55)"
scatter.marker = {
    "radius": 8,
    "symbol": "circle",
    "lineWidth": 1,
    "lineColor": "#ffffff",
    "states": {"hover": {"radiusPlus": 4, "lineWidthPlus": 1, "lineColor": "#306998"}},
}
scatter.z_index = 2

# Model curve using LineSeries (dense sampling makes it smooth without spline overshoot)
model_line = LineSeries()
model_line.data = [[round(float(p), 5), round(float(f), 6)] for p, f in zip(model_phase, model_curve, strict=True)]
model_line.name = "Transit Model"
model_line.color = "#c0392b"
model_line.line_width = 5
model_line.marker = {"enabled": False}
model_line.z_index = 3

chart.add_series(error_band)
chart.add_series(scatter)
chart.add_series(model_line)

# Annotation — transit depth label at the dip
chart.options.annotations = [
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "rgba(255, 255, 255, 0.92)",
                "borderColor": "#c0392b",
                "borderRadius": 8,
                "borderWidth": 2,
                "padding": 14,
                "style": {"fontSize": "34px", "color": "#2c3e50"},
            },
            "labels": [
                {
                    "point": {"x": float(transit_center), "y": float(min_model_flux), "xAxis": 0, "yAxis": 0},
                    "text": f"Transit depth: {depth_ppm:.0f} ppm",
                    "y": 60,
                }
            ],
        }
    )
]

# Download Highcharts JS, highcharts-more, and annotations module
js_urls = [
    ("https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"),
    ("https://code.highcharts.com/highcharts-more.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js"),
    (
        "https://code.highcharts.com/modules/annotations.js",
        "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js",
    ),
]
js_parts = []
for primary, fallback in js_urls:
    for url in (primary, fallback):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                js_parts.append(response.read().decode("utf-8"))
            break
        except Exception:
            continue

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
# Replace backtick template literals with single quotes (backticks can conflict with inline JS)
html_str = html_str.replace("``", "''")
html_content = (
    '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="utf-8">\n'
    "    <script>" + js_parts[0] + "</script>\n"
    "    <script>" + js_parts[1] + "</script>\n"
    "    <script>" + js_parts[2] + "</script>\n"
    '</head>\n<body style="margin:0; background:#fafbfc;">\n'
    '    <div id="container" style="width: 4800px; height: 2700px;"></div>\n'
    "    <script>" + html_str + "</script>\n"
    "</body>\n</html>"
)

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML (CDN links for browser use)
interactive_html = (
    '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="utf-8">\n'
    '    <script src="https://code.highcharts.com/highcharts.js"></script>\n'
    '    <script src="https://code.highcharts.com/highcharts-more.js"></script>\n'
    '    <script src="https://code.highcharts.com/modules/annotations.js"></script>\n'
    '</head>\n<body style="margin:0; background:#fafbfc;">\n'
    '    <div id="container" style="width: 100%; height: 100vh;"></div>\n'
    "    <script>" + html_str + "</script>\n"
    "</body>\n</html>"
)
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(interactive_html)

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Screenshot the chart container for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
