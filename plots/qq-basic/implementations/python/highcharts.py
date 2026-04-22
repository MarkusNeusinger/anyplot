""" pyplots.ai
qq-basic: Basic Q-Q Plot
Library: highcharts unknown | Python 3.13.11
Quality: 90/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from scipy.stats import norm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - generate sample with mix of normal + slight skewness to show Q-Q characteristics
np.random.seed(42)
n = 100
# Create slightly skewed data to demonstrate Q-Q plot interpretation
sample = np.concatenate(
    [
        np.random.randn(80) * 15 + 50,  # Main normal-ish data
        np.random.randn(20) * 10 + 75,  # Some higher values (slight right skew)
    ]
)
np.random.shuffle(sample)

# Calculate Q-Q values
sample_sorted = np.sort(sample)
n_points = len(sample_sorted)
theoretical_quantiles = norm.ppf((np.arange(n_points) + 0.5) / n_points)
# Scale theoretical quantiles to sample scale
sample_mean = np.mean(sample)
sample_std = np.std(sample)
theoretical_scaled = theoretical_quantiles * sample_std + sample_mean

# Reference line (y = x on the scaled theoretical values)
line_min = min(theoretical_scaled.min(), sample_sorted.min())
line_max = max(theoretical_scaled.max(), sample_sorted.max())

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "spacingBottom": 30,
}

# Title (required format: spec-id · library · pyplots.ai)
chart.options.title = {
    "text": "qq-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Axes (scaled for 4800x2700 px)
chart.options.x_axis = {
    "title": {"text": "Theoretical Quantiles", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
    "gridLineDashStyle": "Dash",
    "min": line_min - 5,
    "max": line_max + 5,
}
chart.options.y_axis = {
    "title": {"text": "Sample Quantiles", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
    "gridLineDashStyle": "Dash",
    "min": line_min - 5,
    "max": line_max + 5,
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
}
chart.options.credits = {"enabled": False}

# Reference line (45-degree line) - drawn first so it's behind points
line_series = LineSeries()
line_series.data = [[float(line_min - 5), float(line_min - 5)], [float(line_max + 5), float(line_max + 5)]]
line_series.name = "Reference Line (y=x)"
line_series.color = "#FFD43B"  # Python Yellow
line_series.line_width = 6
line_series.marker = {"enabled": False}
line_series.enable_mouse_tracking = False
line_series.dash_style = "Dash"

chart.add_series(line_series)

# Q-Q scatter points
scatter_series = ScatterSeries()
scatter_series.data = [[float(t), float(s)] for t, s in zip(theoretical_scaled, sample_sorted, strict=True)]
scatter_series.name = "Sample Quantiles (N=100)"
scatter_series.color = "rgba(48, 105, 152, 0.7)"  # Python Blue with alpha
scatter_series.marker = {"radius": 18, "symbol": "circle"}

chart.add_series(scatter_series)

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
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Take screenshot of just the chart container element
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    interactive_html = f"""<!DOCTYPE html>
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
    f.write(interactive_html)
