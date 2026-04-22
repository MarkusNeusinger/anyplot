""" pyplots.ai
bar-diverging: Diverging Bar Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
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
from selenium.webdriver.common.by import By


# Data - Customer satisfaction survey results by department
categories = [
    "Customer Service",
    "IT Support",
    "Sales",
    "Marketing",
    "Finance",
    "Operations",
    "HR",
    "R&D",
    "Legal",
    "Logistics",
]

# Net satisfaction scores: positive = more satisfied than dissatisfied
values = [45, 32, 28, 15, 8, -5, -12, -18, -25, -38]

# Separate positive and negative for different colors
positive_data = [{"y": v, "color": "#306998"} if v >= 0 else {"y": v, "color": "#FFD43B"} for v in values]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "bar",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 280,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "bar-diverging · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {"text": "Department Net Satisfaction Scores", "style": {"fontSize": "32px"}}

# X-axis (categories)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "28px"}},
    "lineWidth": 0,
    "tickWidth": 0,
}

# Y-axis (values) - note: in horizontal bar, y_axis shows values
chart.options.y_axis = {
    "title": {"text": "Net Satisfaction Score", "style": {"fontSize": "28px"}, "margin": 20},
    "labels": {"style": {"fontSize": "24px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "plotLines": [{"value": 0, "width": 3, "color": "#333333", "zIndex": 5}],
    "min": -50,
    "max": 60,
}

# Legend
chart.options.legend = {"enabled": False}

# Credits
chart.options.credits = {"enabled": False}

# Series
series = BarSeries()
series.name = "Net Satisfaction"
series.data = positive_data
series.data_labels = {"enabled": True, "style": {"fontSize": "22px", "fontWeight": "bold"}, "format": "{y}"}
series.border_width = 0
series.point_width = 60

chart.add_series(series)

# Plot options
chart.options.plot_options = {"bar": {"groupPadding": 0.1, "pointPadding": 0.05}}

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
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Get the container element and screenshot it at exact dimensions
container = driver.find_element(By.ID, "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
