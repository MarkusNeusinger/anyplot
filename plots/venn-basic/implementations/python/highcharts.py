""" pyplots.ai
venn-basic: Venn Diagram
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-29
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.venn import VennSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Download Highcharts JS and Venn module (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

venn_url = "https://code.highcharts.com/modules/venn.js"
with urllib.request.urlopen(venn_url, timeout=30) as response:
    venn_js = response.read().decode("utf-8")

# Data: Three programming skill sets with realistic overlaps
# Set A: Backend developers (100), Set B: Frontend developers (80), Set C: DevOps engineers (60)
venn_data = [
    {"sets": ["Backend"], "value": 100},
    {"sets": ["Frontend"], "value": 80},
    {"sets": ["DevOps"], "value": 60},
    {"sets": ["Backend", "Frontend"], "value": 30},
    {"sets": ["Backend", "DevOps"], "value": 20},
    {"sets": ["Frontend", "DevOps"], "value": 15},
    {"sets": ["Backend", "Frontend", "DevOps"], "value": 10},
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
chart.options.chart = {"type": "venn", "width": 4800, "height": 2700, "backgroundColor": "#ffffff"}

# Title
chart.options.title = {
    "text": "venn-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Developer Skill Distribution (Team of 150)", "style": {"fontSize": "32px"}}

# Create Venn series
series = VennSeries()
series.data = venn_data
series.name = "Team Skills"

# Series styling
series.data_labels = {
    "enabled": True,
    "style": {"fontSize": "28px", "fontWeight": "normal", "textOutline": "none"},
    "format": "{point.name}: {point.value}",
}

# Colors: Python Blue, Python Yellow, and a complementary purple
chart.options.colors = ["#306998", "#FFD43B", "#9467BD"]

chart.add_series(series)

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "24px"}}

# Accessibility
chart.options.accessibility = {"enabled": False}

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{venn_js}</script>
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
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    # Use CDN for the HTML file (works in browsers)
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>venn-basic - highcharts - pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/venn.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
