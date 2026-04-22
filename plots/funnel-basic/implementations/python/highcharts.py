""" pyplots.ai
funnel-basic: Basic Funnel Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.funnel import FunnelSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Sales funnel example
stages = ["Awareness", "Interest", "Consideration", "Intent", "Purchase"]
values = [1000, 600, 400, 200, 100]

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 px
chart.options.chart = {
    "type": "funnel",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 150,
}

# Title
chart.options.title = {
    "text": "funnel-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Colorblind-safe colors for each stage
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF", "#8C564B"]

# Create funnel series with data
series = FunnelSeries()
series.name = "Sales Funnel"
series.data = [
    {"name": stage, "y": value, "color": colors[i]} for i, (stage, value) in enumerate(zip(stages, values, strict=True))
]

# Configure data labels to show values and percentages
series.data_labels = {
    "enabled": True,
    "format": "<b>{point.name}</b>: {point.y:,.0f} ({point.percentage:.1f}%)",
    "style": {"fontSize": "36px", "fontWeight": "normal", "textOutline": "2px white"},
    "softConnector": True,
}

# Configure funnel appearance
series.neck_width = "30%"
series.neck_height = "25%"
series.width = "80%"

chart.add_series(series)

# Legend configuration
chart.options.legend = {"enabled": False}

# Plot options for funnel
chart.options.plot_options = {"funnel": {"dataLabels": {"enabled": True, "style": {"fontSize": "36px"}}}}

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS and funnel module for headless Chrome
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

funnel_url = "https://code.highcharts.com/modules/funnel.js"
with urllib.request.urlopen(funnel_url, timeout=30) as response:
    funnel_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{funnel_js}</script>
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

# Save HTML for interactive version (use CDN for portability)
html_cdn = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/funnel.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_cdn)

# Configure headless Chrome
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
