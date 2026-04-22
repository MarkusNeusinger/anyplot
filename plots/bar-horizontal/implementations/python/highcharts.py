""" pyplots.ai
bar-horizontal: Horizontal Bar Chart
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Top 10 countries by renewable energy share (2024)
categories = [
    "Iceland",
    "Norway",
    "Brazil",
    "New Zealand",
    "Sweden",
    "Canada",
    "Finland",
    "Austria",
    "Denmark",
    "Switzerland",
]
values = [85.0, 71.5, 65.2, 58.4, 54.8, 52.1, 47.3, 43.6, 41.2, 38.5]

# Sort by value (largest at top for horizontal bar chart)
sorted_pairs = sorted(zip(categories, values, strict=True), key=lambda x: x[1])
categories = [p[0] for p in sorted_pairs]
values = [p[1] for p in sorted_pairs]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
chart.options.chart = {
    "type": "bar",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 250,
    "marginRight": 200,
    "marginBottom": 180,
    "marginTop": 180,
}

# Title
chart.options.title = {
    "text": "bar-horizontal · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Top 10 Countries by Renewable Energy Share (%)", "style": {"fontSize": "32px"}}

# X-axis (categories on y-axis for horizontal bar)
chart.options.x_axis = {"categories": categories, "title": {"text": None}, "labels": {"style": {"fontSize": "28px"}}}

# Y-axis (values - appears at bottom for bar chart)
chart.options.y_axis = {
    "min": 0,
    "max": 100,
    "title": {"text": "Renewable Energy Share (%)", "style": {"fontSize": "32px"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px"}, "format": "{value}%"},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Plot options
chart.options.plot_options = {
    "bar": {
        "dataLabels": {"enabled": True, "format": "{y}%", "style": {"fontSize": "24px", "fontWeight": "normal"}},
        "pointPadding": 0.1,
        "groupPadding": 0.1,
        "borderWidth": 0,
        "borderRadius": 4,
    }
}

# Legend
chart.options.legend = {"enabled": False}

# Credits
chart.options.credits = {"enabled": False}

# Series
series = BarSeries()
series.name = "Renewable Energy Share"
series.data = values
series.color = "#306998"

chart.add_series(series)

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

# Write temp HTML file
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save standalone HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")
chrome_options.add_argument("--hide-scrollbars")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Screenshot the chart container element directly for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
