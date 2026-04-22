""" pyplots.ai
line-stepwise: Step Line Plot
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
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Server response time over monitoring period (discrete changes)
np.random.seed(42)
hours = np.arange(0, 24)
# Simulate server response times that change discretely throughout the day
base_response = 45
response_times = np.zeros(24)
response_times[0:6] = base_response + np.random.randint(0, 10, 6)  # Night: low load
response_times[6:9] = base_response + 25 + np.random.randint(0, 15, 3)  # Morning spike
response_times[9:12] = base_response + 15 + np.random.randint(0, 10, 3)  # Mid-morning
response_times[12:14] = base_response + 30 + np.random.randint(0, 20, 2)  # Lunch peak
response_times[14:17] = base_response + 20 + np.random.randint(0, 15, 3)  # Afternoon
response_times[17:20] = base_response + 35 + np.random.randint(0, 20, 3)  # Evening peak
response_times[20:24] = base_response + 5 + np.random.randint(0, 10, 4)  # Night decline

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 px
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 180,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "line-stepwise · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {"text": "Server Response Time (24-Hour Monitoring)", "style": {"fontSize": "32px"}}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "Hour of Day", "style": {"fontSize": "40px"}, "margin": 20},
    "labels": {"style": {"fontSize": "28px"}, "y": 35},
    "categories": [f"{h:02d}:00" for h in hours],
    "tickInterval": 2,
    "lineWidth": 2,
    "tickWidth": 2,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Response Time (ms)", "style": {"fontSize": "40px"}, "margin": 20},
    "labels": {"style": {"fontSize": "28px"}, "x": -10},
    "min": 40,
    "max": 100,
    "gridLineColor": "#e0e0e0",
    "gridLineWidth": 1,
    "lineWidth": 2,
}

# Plot options - enable step line
chart.options.plot_options = {
    "line": {
        "step": "left",  # Step before the point (horizontal-then-vertical)
        "lineWidth": 6,
        "marker": {"enabled": True, "radius": 12, "symbol": "circle"},
    }
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "align": "right",
    "verticalAlign": "top",
    "x": -50,
    "y": 100,
}

# Create series
series = LineSeries()
series.name = "Response Time"
series.data = [float(v) for v in response_times]
series.color = "#306998"  # Python Blue
series.marker = {"fillColor": "#306998", "lineWidth": 2, "lineColor": "#ffffff"}

chart.add_series(series)

# Download Highcharts JS for headless Chrome
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

# Also save the HTML file for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    # For the saved HTML, use CDN for broader compatibility
    html_cdn = (
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>"""
        + html_str
        + """</script>
</body>
</html>"""
    )
    f.write(html_cdn)

# Take screenshot with headless Chrome
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
