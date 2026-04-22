""" pyplots.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: highcharts unknown | Python 3.13.11
Quality: 93/100 | Created: 2025-12-25
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


# Data - Simulating diminishing returns (e.g., advertising spend vs revenue)
np.random.seed(42)
n_points = 80
x = np.linspace(1, 20, n_points)
# Quadratic relationship with diminishing returns: y = -0.3x² + 10x + 5
y_true = -0.3 * x**2 + 10 * x + 5
noise = np.random.normal(0, 5, n_points)
y = y_true + noise

# Fit polynomial regression (degree 2)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)
x_fit = np.linspace(x.min(), x.max(), 200)
y_fit = poly(x_fit)

# Calculate R² value
y_pred = poly(x)
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Format equation
a, b, c = coeffs
equation = f"y = {a:.3f}x² + {b:.3f}x + {c:.3f}"

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingBottom": 50,
    "spacingTop": 50,
    "spacingLeft": 50,
    "spacingRight": 50,
}

# Title with spec-id format
chart.options.title = {
    "text": "scatter-regression-polynomial · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle showing equation and R²
chart.options.subtitle = {
    "text": f"{equation} | R² = {r_squared:.4f}",
    "style": {"fontSize": "36px", "color": "#666666"},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Advertising Spend ($k)", "style": {"fontSize": "36px"}, "margin": 30},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "lineWidth": 2,
    "tickWidth": 2,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Revenue ($k)", "style": {"fontSize": "36px"}, "margin": 30},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "lineWidth": 2,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 100,
    "floating": True,
    "backgroundColor": "rgba(255,255,255,0.9)",
    "borderWidth": 1,
    "borderColor": "#cccccc",
    "itemStyle": {"fontSize": "28px"},
    "itemMarginTop": 10,
    "itemMarginBottom": 10,
}

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "24px"},
    "headerFormat": "",
    "pointFormat": "Spend: ${point.x:.1f}k<br/>Revenue: ${point.y:.1f}k",
}

# Scatter series (data points)
scatter_series = ScatterSeries()
scatter_series.data = [[float(xi), float(yi)] for xi, yi in zip(x, y, strict=True)]
scatter_series.name = "Data Points"
scatter_series.marker = {"radius": 12, "fillColor": "rgba(48, 105, 152, 0.65)", "lineWidth": 2, "lineColor": "#306998"}
scatter_series.color = "#306998"

# Regression curve (spline for smooth curve)
regression_series = SplineSeries()
regression_series.data = [[float(xi), float(yi)] for xi, yi in zip(x_fit, y_fit, strict=True)]
regression_series.name = f"Polynomial Fit (R² = {r_squared:.3f})"
regression_series.color = "#FFD43B"
regression_series.lineWidth = 5
regression_series.marker = {"enabled": False}

# Add series
chart.add_series(scatter_series)
chart.add_series(regression_series)

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

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Selenium screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Take screenshot of the container element for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
