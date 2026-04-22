""" pyplots.ai
scatter-basic: Basic Scatter Plot
Library: highcharts 1.10.3 | Python 3.14
Quality: 91/100 | Created: 2025-12-22
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.annotations import Annotation
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data — height vs weight with moderate positive correlation
np.random.seed(42)
n_points = 100
height_cm = np.random.normal(170, 10, n_points)
weight_kg = height_cm * 0.65 + np.random.normal(0, 5, n_points) - 40

# Compute linear regression for trend line
slope, intercept = np.polyfit(height_cm, weight_kg, 1)
r_squared = np.corrcoef(height_cm, weight_kg)[0, 1] ** 2

# Axis bounds — tight to data with small padding
x_min, x_max = float(np.floor(height_cm.min() - 2)), float(np.ceil(height_cm.max() + 2))
y_min, y_max = float(np.floor(weight_kg.min() - 3)), float(np.ceil(weight_kg.max() + 3))

# Trend line endpoints
trend_x = np.array([x_min, x_max])
trend_y = slope * trend_x + intercept

# Identify outlier points (beyond 2 std from regression line)
predicted = slope * height_cm + intercept
residuals = weight_kg - predicted
std_resid = np.std(residuals)
outlier_mask = np.abs(residuals) > 1.8 * std_resid
outlier_heights = height_cm[outlier_mask]
outlier_weights = weight_kg[outlier_mask]

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
    "marginBottom": 310,
    "marginLeft": 220,
    "marginRight": 200,
}

# Title with refined typography
chart.options.title = {
    "text": "scatter-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "600", "color": "#2c3e50", "letterSpacing": "1px"},
    "margin": 50,
}

# Subtitle for data storytelling
chart.options.subtitle = {
    "text": "Height vs Weight — positive correlation across 100 subjects",
    "style": {"fontSize": "38px", "color": "#7f8c8d", "fontWeight": "400"},
}

# X-axis with tight bounds and refined styling
chart.options.x_axis = {
    "title": {
        "text": "Height (cm)",
        "style": {"fontSize": "44px", "color": "#34495e", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#7f8c8d"}},
    "min": x_min,
    "max": x_max,
    "tickInterval": 5,
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

# Y-axis with tight bounds and reduced tick density
chart.options.y_axis = {
    "title": {
        "text": "Weight (kg)",
        "style": {"fontSize": "44px", "color": "#34495e", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "34px", "color": "#7f8c8d"}},
    "min": y_min,
    "max": y_max,
    "tickInterval": 5,
    "startOnTick": False,
    "endOnTick": False,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#bdc3c7",
    "lineWidth": 2,
    "tickColor": "#bdc3c7",
    "tickLength": 10,
    "plotBands": [
        {
            "from": y_min,
            "to": float(np.percentile(weight_kg, 25)),
            "color": "rgba(48, 105, 152, 0.03)",
            "label": {
                "text": "Lower quartile",
                "style": {"fontSize": "32px", "color": "rgba(48, 105, 152, 0.55)"},
                "align": "left",
                "x": 20,
                "y": 16,
            },
        },
        {
            "from": float(np.percentile(weight_kg, 75)),
            "to": y_max,
            "color": "rgba(48, 105, 152, 0.03)",
            "label": {
                "text": "Upper quartile",
                "style": {"fontSize": "32px", "color": "rgba(48, 105, 152, 0.55)"},
                "align": "left",
                "x": 20,
                "y": 16,
            },
        },
    ],
}

# Legend — show to label trend line
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

# Rich tooltip — Highcharts-distinctive feature
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": (
        '<span style="font-size:24px;color:{point.color}">\u25cf</span> '
        '<span style="font-size:26px">'
        "Height: <b>{point.x:.1f} cm</b><br/>"
        "Weight: <b>{point.y:.1f} kg</b></span>"
    ),
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 10,
    "borderWidth": 2,
    "shadow": {"color": "rgba(0,0,0,0.1)", "offsetX": 2, "offsetY": 2, "width": 4},
    "style": {"fontSize": "26px"},
}

# Main scatter series — Python Blue with transparency
scatter = ScatterSeries()
scatter.data = [[float(h), float(w)] for h, w in zip(height_cm, weight_kg, strict=True)]
scatter.name = "Subjects"
scatter.color = "rgba(48, 105, 152, 0.65)"
scatter.marker = {
    "radius": 12,
    "symbol": "circle",
    "lineWidth": 2,
    "lineColor": "#ffffff",
    "states": {"hover": {"radiusPlus": 4, "lineWidthPlus": 1, "lineColor": "#306998"}},
}
scatter.z_index = 2

# Outlier series — highlight extreme points with distinct marker
outlier_series = ScatterSeries()
outlier_series.data = [[float(h), float(w)] for h, w in zip(outlier_heights, outlier_weights, strict=True)]
outlier_series.name = "Outliers"
outlier_series.color = "rgba(211, 84, 0, 0.80)"
outlier_series.marker = {
    "radius": 15,
    "symbol": "diamond",
    "lineWidth": 2,
    "lineColor": "#d35400",
    "states": {"hover": {"radiusPlus": 4}},
}
outlier_series.z_index = 3

# Trend line (linear regression) using SplineSeries
trend = SplineSeries()
trend.data = [[float(trend_x[0]), float(trend_y[0])], [float(trend_x[1]), float(trend_y[1])]]
trend.name = f"Trend (R\u00b2 = {r_squared:.2f})"
trend.color = "#e67e22"
trend.line_width = 4
trend.dash_style = "LongDash"
trend.marker = {"enabled": False}
trend.enable_mouse_tracking = False
trend.z_index = 1

chart.add_series(scatter)
chart.add_series(outlier_series)
chart.add_series(trend)

# Annotation — R² value and slope description
chart.options.annotations = [
    Annotation.from_dict(
        {
            "draggable": "",
            "labelOptions": {
                "backgroundColor": "rgba(255, 255, 255, 0.9)",
                "borderColor": "#e67e22",
                "borderRadius": 8,
                "borderWidth": 2,
                "padding": 14,
                "style": {"fontSize": "34px", "color": "#2c3e50"},
            },
            "labels": [
                {
                    "point": {
                        "x": float(x_min + 8),
                        "y": float(slope * (x_min + 8) + intercept - 5),
                        "xAxis": 0,
                        "yAxis": 0,
                    },
                    "text": f"y = {slope:.2f}x {intercept:+.1f}  |  R\u00b2 = {r_squared:.2f}",
                }
            ],
        }
    )
]

# Download Highcharts JS and annotations module (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
annotations_url = "https://code.highcharts.com/modules/annotations.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Screenshot the chart container for exact dimensions
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
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
