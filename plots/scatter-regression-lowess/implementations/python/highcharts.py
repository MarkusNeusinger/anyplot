""" pyplots.ai
scatter-regression-lowess: Scatter Plot with LOWESS Regression
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
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


def lowess(x, y, frac=0.3):
    """Simple LOWESS implementation using tricube weighting."""
    n = len(x)
    k = int(np.ceil(frac * n))  # Number of neighbors to use
    y_smooth = np.zeros(n)
    sorted_idx = np.argsort(x)
    x_sorted = x[sorted_idx]
    y_sorted = y[sorted_idx]

    for i in range(n):
        # Calculate distances to all points
        distances = np.abs(x_sorted - x_sorted[i])
        # Find k nearest neighbors
        nearest_idx = np.argsort(distances)[:k]
        # Maximum distance among neighbors
        max_dist = distances[nearest_idx[-1]]
        if max_dist == 0:
            max_dist = 1.0
        # Tricube weights
        u = distances[nearest_idx] / max_dist
        weights = (1 - u**3) ** 3
        # Weighted linear regression
        x_local = x_sorted[nearest_idx]
        y_local = y_sorted[nearest_idx]
        # Weighted least squares
        w_sum = np.sum(weights)
        wx_sum = np.sum(weights * x_local)
        wy_sum = np.sum(weights * y_local)
        wxx_sum = np.sum(weights * x_local * x_local)
        wxy_sum = np.sum(weights * x_local * y_local)
        # Solve for slope and intercept
        denom = w_sum * wxx_sum - wx_sum**2
        if abs(denom) < 1e-10:
            y_smooth[i] = wy_sum / w_sum if w_sum > 0 else y_sorted[i]
        else:
            slope = (w_sum * wxy_sum - wx_sum * wy_sum) / denom
            intercept = (wy_sum - slope * wx_sum) / w_sum
            y_smooth[i] = slope * x_sorted[i] + intercept

    # Return in original order
    result = np.zeros(n)
    result[sorted_idx] = y_smooth
    return x, result


# Data - Generate complex non-linear relationship
np.random.seed(42)
n_points = 200
x = np.linspace(0, 10, n_points)
# Create a complex non-linear pattern: sine wave + quadratic + noise
y = 3 * np.sin(x * 1.2) + 0.3 * x**2 - 0.5 * x + np.random.normal(0, 1.5, n_points)

# Compute LOWESS regression curve
x_lowess, y_lowess = lowess(x, y, frac=0.3)

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 150,
    "spacingTop": 60,
    "spacingRight": 100,
}

# Title
chart.options.title = {
    "text": "scatter-regression-lowess · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle with context
chart.options.subtitle = {"text": "Non-linear Trend with LOWESS Smoothing (frac=0.3)", "style": {"fontSize": "32px"}}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "X Value", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Y Value", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
}

# Plot options
chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 10, "fillColor": "rgba(48, 105, 152, 0.6)", "lineWidth": 1, "lineColor": "#306998"}
    },
    "spline": {"marker": {"enabled": False}, "lineWidth": 5},
}

# Add scatter series (data points)
scatter_series = ScatterSeries()
scatter_series.name = "Data Points"
scatter_series.data = [[float(xi), float(yi)] for xi, yi in zip(x, y, strict=True)]
scatter_series.color = "#306998"
chart.add_series(scatter_series)

# Add LOWESS curve as spline series
lowess_series = SplineSeries()
lowess_series.name = "LOWESS Curve"
lowess_series.data = [[float(xi), float(yi)] for xi, yi in zip(x_lowess, y_lowess, strict=True)]
lowess_series.color = "#FFD43B"
lowess_series.marker = {"enabled": False}
lowess_series.line_width = 6
chart.add_series(lowess_series)

# Download Highcharts JS for inline embedding
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

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Configure Chrome for headless screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
