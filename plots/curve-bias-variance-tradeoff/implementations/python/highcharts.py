""" pyplots.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2026-01-26
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Generate theoretical bias-variance tradeoff curves
complexity = np.linspace(0.5, 10, 100)

# Bias squared: decreases with complexity (high bias = underfitting)
bias_squared = 2.0 / (1 + 0.5 * complexity)

# Variance: increases with complexity (high variance = overfitting)
variance = 0.1 * complexity**1.5

# Irreducible error: constant noise floor
irreducible_error = np.full_like(complexity, 0.3)

# Total error: sum of all components
total_error = bias_squared + variance + irreducible_error

# Find optimal complexity (minimum total error)
optimal_idx = np.argmin(total_error)
optimal_complexity = complexity[optimal_idx]
optimal_error = total_error[optimal_idx]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "spline",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 280,
    "marginLeft": 200,
    "marginRight": 300,
    "spacingBottom": 60,
}

# Title
chart.options.title = {
    "text": "curve-bias-variance-tradeoff \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle with formula
chart.options.subtitle = {
    "text": "Total Error = Bias\u00b2 + Variance + Irreducible Error",
    "style": {"fontSize": "32px", "color": "#666666"},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Model Complexity", "style": {"fontSize": "36px", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 10.5,
    "tickInterval": 1,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "plotBands": [
        {
            "from": 0,
            "to": optimal_complexity,
            "color": "rgba(48, 105, 152, 0.08)",
            "label": {
                "text": "Underfitting<br>(High Bias)",
                "style": {"fontSize": "28px", "color": "#306998"},
                "verticalAlign": "bottom",
                "y": -60,
            },
        },
        {
            "from": optimal_complexity,
            "to": 11,
            "color": "rgba(255, 212, 59, 0.12)",
            "label": {
                "text": "Overfitting<br>(High Variance)",
                "style": {"fontSize": "28px", "color": "#B8860B"},
                "verticalAlign": "bottom",
                "y": -60,
            },
        },
    ],
    "plotLines": [
        {
            "value": optimal_complexity,
            "color": "#2ECC71",
            "width": 4,
            "dashStyle": "Dash",
            "label": {
                "text": "Optimal<br>Complexity",
                "style": {"fontSize": "26px", "color": "#2ECC71", "fontWeight": "bold"},
                "rotation": 0,
                "y": 60,
                "x": 10,
            },
            "zIndex": 5,
        }
    ],
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Prediction Error", "style": {"fontSize": "36px", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 3.5,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "28px", "fontWeight": "normal"},
    "symbolWidth": 40,
    "symbolHeight": 20,
    "itemMarginBottom": 15,
}

# Plot options
chart.options.plot_options = {
    "spline": {"lineWidth": 5, "marker": {"enabled": False}},
    "scatter": {"marker": {"radius": 16, "symbol": "circle"}},
}

# Tooltip
chart.options.tooltip = {
    "headerFormat": "<b>Complexity: {point.x:.1f}</b><br/>",
    "pointFormat": "{series.name}: <b>{point.y:.3f}</b>",
    "style": {"fontSize": "24px"},
}

# Create series - Using from_array for proper data handling
# Bias squared curve
bias_series = AreaSeries()
bias_series.name = "Bias\u00b2"
bias_series.data = [[float(x), float(y)] for x, y in zip(complexity, bias_squared, strict=True)]
bias_series.color = "#306998"
bias_series.fill_opacity = 0
chart.add_series(bias_series)

# Variance curve
variance_series = AreaSeries()
variance_series.name = "Variance"
variance_series.data = [[float(x), float(y)] for x, y in zip(complexity, variance, strict=True)]
variance_series.color = "#FFD43B"
variance_series.fill_opacity = 0
chart.add_series(variance_series)

# Irreducible error curve
irreducible_series = AreaSeries()
irreducible_series.name = "Irreducible Error"
irreducible_series.data = [[float(x), float(y)] for x, y in zip(complexity, irreducible_error, strict=True)]
irreducible_series.color = "#9467BD"
irreducible_series.fill_opacity = 0
irreducible_series.dash_style = "Dot"
chart.add_series(irreducible_series)

# Total error curve (most prominent)
total_series = AreaSeries()
total_series.name = "Total Error"
total_series.data = [[float(x), float(y)] for x, y in zip(complexity, total_error, strict=True)]
total_series.color = "#E74C3C"
total_series.fill_opacity = 0
total_series.line_width = 7
chart.add_series(total_series)

# Optimal point marker
optimal_series = ScatterSeries()
optimal_series.name = "Optimal Point"
optimal_series.data = [[float(optimal_complexity), float(optimal_error)]]
optimal_series.color = "#2ECC71"
optimal_series.marker = {"radius": 18, "symbol": "diamond", "lineWidth": 3, "lineColor": "#ffffff"}
chart.add_series(optimal_series)

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
