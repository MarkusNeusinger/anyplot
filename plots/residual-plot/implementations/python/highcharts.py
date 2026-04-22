""" pyplots.ai
residual-plot: Residual Plot
Library: highcharts unknown | Python 3.13.11
Quality: 93/100 | Created: 2025-12-26
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Linear regression example with housing price predictions
np.random.seed(42)

# Generate realistic housing data
n_points = 120
square_feet = np.random.uniform(800, 3500, n_points)
base_price = 50000 + 150 * square_feet
noise = np.random.normal(0, 30000, n_points)
y_true = base_price + noise

# Simulate a fitted linear regression
slope = 148
intercept = 52000
y_pred = intercept + slope * square_feet

# Calculate residuals
residuals = y_true - y_pred

# Identify outliers (beyond ±2 std)
std_residual = np.std(residuals)
mean_residual = np.mean(residuals)
outlier_threshold = 2 * std_residual
is_outlier = np.abs(residuals - mean_residual) > outlier_threshold

# Prepare data for regular points and outliers
regular_data = [[float(y_pred[i]), float(residuals[i])] for i in range(n_points) if not is_outlier[i]]
outlier_data = [[float(y_pred[i]), float(residuals[i])] for i in range(n_points) if is_outlier[i]]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration - increased margins for better label visibility
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 280,
    "marginLeft": 280,
    "marginTop": 150,
    "marginRight": 220,
    "spacingBottom": 50,
}

# Title
chart.options.title = {
    "text": "residual-plot · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# X-axis (Fitted Values)
x_min = float(min(y_pred))
x_max = float(max(y_pred))
chart.options.x_axis = {
    "title": {"text": "Fitted Values ($)", "style": {"fontSize": "42px", "fontWeight": "bold"}, "margin": 40},
    "labels": {"style": {"fontSize": "32px"}, "rotation": 0, "y": 35},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
    "min": x_min - 10000,
    "max": x_max + 10000,
    "tickInterval": 50000,
}

# Y-axis (Residuals) - use actual data extent with small buffer, keeping zero visible
y_min = float(min(residuals))
y_max = float(max(residuals))
y_axis_min = y_min * 1.1  # 10% buffer below min
y_axis_max = y_max * 1.1  # 10% buffer above max
chart.options.y_axis = {
    "title": {"text": "Residuals ($)", "style": {"fontSize": "42px", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "32px"}, "x": -10},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
    "min": y_axis_min,
    "max": y_axis_max,
    "tickInterval": 20000,
    "endOnTick": False,
    "startOnTick": False,
    "plotLines": [
        {
            "value": 0,
            "color": "#306998",
            "width": 5,
            "zIndex": 5,
            "label": {
                "text": "Zero Line (Perfect Fit)",
                "align": "right",
                "x": -15,
                "style": {"fontSize": "36px", "color": "#306998", "fontWeight": "bold"},
            },
        },
        {
            "value": float(outlier_threshold),
            "color": "#E67E22",
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 4,
            "label": {
                "text": "+2\u03c3 Threshold",
                "align": "right",
                "x": -15,
                "style": {"fontSize": "36px", "color": "#E67E22", "fontWeight": "bold"},
            },
        },
        {
            "value": float(-outlier_threshold),
            "color": "#E67E22",
            "width": 4,
            "dashStyle": "Dash",
            "zIndex": 4,
            "label": {
                "text": "-2\u03c3 Threshold",
                "align": "right",
                "x": -15,
                "style": {"fontSize": "36px", "color": "#E67E22", "fontWeight": "bold"},
            },
        },
    ],
}

# Legend - position at top right with larger, more readable text
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 100,
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal"},
    "symbolRadius": 8,
    "symbolWidth": 32,
    "symbolHeight": 32,
    "itemMarginBottom": 12,
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderWidth": 2,
    "borderColor": "#cccccc",
    "padding": 20,
}

# Plot options
chart.options.plot_options = {
    "scatter": {
        "marker": {"radius": 12, "symbol": "circle"},
        "states": {"hover": {"enabled": True, "lineWidthPlus": 0}},
    }
}

# Regular points series
regular_series = ScatterSeries()
regular_series.name = "Residuals"
regular_series.data = regular_data
regular_series.color = "#306998"
regular_series.marker = {"radius": 12, "fillColor": "rgba(48, 105, 152, 0.6)", "lineWidth": 2, "lineColor": "#306998"}
chart.add_series(regular_series)

# Outlier points series
if outlier_data:
    outlier_series = ScatterSeries()
    outlier_series.name = "Outliers (>2σ)"
    outlier_series.data = outlier_data
    outlier_series.color = "#E74C3C"
    outlier_series.marker = {
        "radius": 16,
        "fillColor": "rgba(231, 76, 60, 0.7)",
        "lineWidth": 3,
        "lineColor": "#C0392B",
        "symbol": "diamond",
    }
    chart.add_series(outlier_series)

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

# Write temp HTML
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Setup Chrome for screenshot
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

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    # Create standalone HTML with CDN for proper interactive version
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>residual-plot · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)

# Cleanup
Path(temp_path).unlink()
