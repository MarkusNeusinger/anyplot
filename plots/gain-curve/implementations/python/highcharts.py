""" pyplots.ai
gain-curve: Cumulative Gains Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-29
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Customer response model with predicted probabilities
np.random.seed(42)
n_samples = 1000

# Simulate a classification model with varying discrimination
# Create a mix of strong and weak signals
positive_rate = 0.15  # 15% positive class
n_positives = int(n_samples * positive_rate)
n_negatives = n_samples - n_positives

# Generate predicted probabilities
# Positives tend to have higher scores, but with overlap
positive_scores = np.random.beta(5, 2, n_positives)  # Higher scores
negative_scores = np.random.beta(2, 5, n_negatives)  # Lower scores

y_true = np.concatenate([np.ones(n_positives), np.zeros(n_negatives)])
y_score = np.concatenate([positive_scores, negative_scores])

# Calculate gain curve
sorted_indices = np.argsort(y_score)[::-1]  # Sort by score descending
sorted_true = y_true[sorted_indices]

# Cumulative gains
cumulative_positives = np.cumsum(sorted_true)
total_positives = cumulative_positives[-1]
gains = cumulative_positives / total_positives * 100

# Population percentages
population_pct = np.arange(1, n_samples + 1) / n_samples * 100

# Subsample for smoother chart display
sample_indices = np.linspace(0, len(population_pct) - 1, 100, dtype=int)
x_values = population_pct[sample_indices].tolist()
y_values = gains[sample_indices].tolist()

# Add starting point
x_values = [0] + x_values
y_values = [0] + y_values

# Random baseline (diagonal)
baseline_x = [0, 100]
baseline_y = [0, 100]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 350,
    "marginLeft": 220,
    "marginTop": 180,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "gain-curve · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Customer Response Model Performance", "style": {"fontSize": "48px"}}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Population Targeted (%)", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Positive Cases Captured (%)", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
}

# Legend (positioned inside chart area)
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "40px"},
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "x": -50,
    "y": 200,
    "symbolWidth": 50,
    "symbolHeight": 25,
    "backgroundColor": "rgba(255, 255, 255, 0.8)",
    "borderWidth": 1,
    "borderColor": "#e0e0e0",
    "padding": 20,
}

# Plot options
chart.options.plot_options = {
    "area": {"lineWidth": 4, "marker": {"enabled": False}},
    "line": {"lineWidth": 4, "marker": {"enabled": False}},
}

# Model gain curve with area fill
gain_series = AreaSeries()
gain_series.data = [[x, y] for x, y in zip(x_values, y_values, strict=True)]
gain_series.name = "Model Gain"
gain_series.color = "#306998"
gain_series.fill_color = {
    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
    "stops": [[0, "rgba(48, 105, 152, 0.5)"], [1, "rgba(48, 105, 152, 0.1)"]],
}
chart.add_series(gain_series)

# Random baseline (dashed diagonal)
baseline_series = SplineSeries()
baseline_series.data = [[x, y] for x, y in zip(baseline_x, baseline_y, strict=True)]
baseline_series.name = "Random Selection"
baseline_series.color = "#FFD43B"
baseline_series.dash_style = "Dash"
chart.add_series(baseline_series)

# Tooltip
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{series.name}</b><br/>Population: {point.x:.1f}%<br/>Captured: {point.y:.1f}%",
    "style": {"fontSize": "24px"},
}

# Download Highcharts JS (required for headless Chrome)
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

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    # Include CDN for HTML file (works in browser)
    html_interactive = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(html_interactive)

driver.quit()
Path(temp_path).unlink()  # Clean up temp file
