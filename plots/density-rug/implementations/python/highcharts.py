""" pyplots.ai
density-rug: Density Plot with Rug Marks
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
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
from scipy.stats import gaussian_kde
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Response times (in milliseconds) for a web service
np.random.seed(42)
# Bimodal distribution to show KDE's ability to reveal multiple modes
fast_responses = np.random.normal(120, 25, 80)
slow_responses = np.random.normal(280, 40, 45)
values = np.concatenate([fast_responses, slow_responses])
values = values[values > 0]  # Ensure positive response times

# Compute KDE
kde = gaussian_kde(values, bw_method=0.2)
x_range = np.linspace(values.min() - 20, values.max() + 20, 300)
density = kde(x_range)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
chart.options.chart = {
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "Arial, sans-serif"},
    "marginBottom": 200,
    "marginLeft": 160,
}

# Title
chart.options.title = {
    "text": "density-rug · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {
    "text": "API Response Time Distribution (ms)",
    "style": {"fontSize": "32px", "color": "#666666"},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Response Time (ms)", "style": {"fontSize": "36px"}, "y": 30},
    "labels": {"style": {"fontSize": "28px"}, "y": 35},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "min": float(x_range.min()),
    "max": float(x_range.max()),
    "tickInterval": 50,
}

# Y-axis - extend minimum to show rug marks below 0
rug_y_position = -max(density) * 0.08
chart.options.y_axis = {
    "title": {"text": "Density", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "24px"}},
    "gridLineColor": "rgba(0, 0, 0, 0.15)",
    "min": rug_y_position * 1.5,  # Allow space for rug marks
    "plotLines": [{"value": 0, "color": "rgba(0, 0, 0, 0.3)", "width": 2, "zIndex": 3}],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "verticalAlign": "top",
    "align": "right",
    "floating": True,
    "y": 60,
}

# Credits off
chart.options.credits = {"enabled": False}

# KDE density curve (Area series with fill)
kde_series = AreaSeries()
kde_series.name = "Density (KDE)"
kde_series.data = [[float(x), float(y)] for x, y in zip(x_range, density, strict=True)]
kde_series.color = "#306998"
kde_series.fill_opacity = 0.4
kde_series.line_width = 4
kde_series.marker = {"enabled": False}

chart.add_series(kde_series)

# Rug marks - scatter points at the bottom
# Place rug marks at a small negative y to sit below the density curve
rug_series = ScatterSeries()
rug_series.name = "Rug (Individual Points)"
rug_series.data = [[float(v), rug_y_position] for v in values]
rug_series.color = "#FFD43B"
rug_series.marker = {"symbol": "diamond", "radius": 12, "fillColor": "#FFD43B", "lineWidth": 2, "lineColor": "#E6B800"}

chart.add_series(rug_series)

# Plot options
chart.options.plot_options = {
    "area": {"states": {"hover": {"enabled": False}}},
    "scatter": {"states": {"hover": {"enabled": False}}},
}

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
<body style="margin:0; background-color: #ffffff;">
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
    # For the HTML version, use CDN
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)

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
