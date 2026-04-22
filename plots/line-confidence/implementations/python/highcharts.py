""" pyplots.ai
line-confidence: Line Plot with Confidence Interval
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Simulated model predictions with 95% confidence interval
np.random.seed(42)
x = np.arange(1, 51)  # 50 data points (days 1-50)
base_trend = 100 + 2.5 * x + 15 * np.sin(x * 0.3)  # Trend with oscillation
noise = np.random.randn(50) * 5  # Random noise
y = base_trend + noise  # Central line (predictions)
uncertainty = 8 + 0.15 * x  # Uncertainty grows over time
y_lower = y - 1.96 * uncertainty  # Lower 95% CI
y_upper = y + 1.96 * uncertainty  # Upper 95% CI

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "Arial, sans-serif"},
    "marginBottom": 250,
    "spacingBottom": 60,
}

# Title
chart.options.title = {
    "text": "line-confidence · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle for context
chart.options.subtitle = {
    "text": "Model Predictions with 95% Confidence Interval",
    "style": {"fontSize": "42px", "color": "#666666"},
}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "Day", "style": {"fontSize": "48px"}, "margin": 30},
    "labels": {"style": {"fontSize": "36px"}, "enabled": True, "y": 40},
    "tickInterval": 5,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Predicted Value", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
    "itemStyle": {"fontSize": "36px"},
    "itemMarginBottom": 15,
}

# Plot options
chart.options.plot_options = {
    "series": {"animation": False},
    "line": {"lineWidth": 6, "marker": {"enabled": False}},
    "arearange": {"fillOpacity": 0.3, "lineWidth": 0, "marker": {"enabled": False}},
}

# Add confidence band (arearange series)
confidence_data = [[int(x[i]), float(y_lower[i]), float(y_upper[i])] for i in range(len(x))]
confidence_series = AreaRangeSeries()
confidence_series.data = confidence_data
confidence_series.name = "95% Confidence Interval"
confidence_series.color = "#306998"
confidence_series.fill_opacity = 0.3

# Add central line
line_data = [[int(x[i]), float(y[i])] for i in range(len(x))]
line_series = LineSeries()
line_series.data = line_data
line_series.name = "Prediction"
line_series.color = "#306998"

# Add series (confidence band first, then line on top)
chart.add_series(confidence_series)
chart.add_series(line_series)

# Download Highcharts JS modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
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

# Also save the HTML file for interactive viewing
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

Path(temp_path).unlink()  # Clean up temp file
