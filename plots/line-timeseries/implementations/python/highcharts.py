""" pyplots.ai
line-timeseries: Time Series Line Plot
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import math
import random
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Daily temperature readings over one year (365 days)
random.seed(42)
start_date = datetime(2024, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(365)]
timestamps = [int(d.timestamp() * 1000) for d in dates]  # Highcharts uses milliseconds

# Realistic temperature pattern with seasonal variation (Northern Hemisphere)
temperatures = []
for d in dates:
    # Base temperature varies seasonally (cold winter, warm summer)
    day_of_year = d.timetuple().tm_yday
    seasonal = 15 * math.sin((day_of_year - 80) * 2 * math.pi / 365)  # Peak around day 170 (June)
    base_temp = 12 + seasonal  # Base around 12°C with ±15°C seasonal swing

    # Add some daily variation (noise)
    daily_noise = random.gauss(0, 2.5)

    temperatures.append(round(base_temp + daily_noise, 1))

# Combine timestamps and values for Highcharts
data_points = list(zip(timestamps, temperatures, strict=True))

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "spacingTop": 60,
    "spacingBottom": 100,
    "spacingLeft": 80,
    "spacingRight": 80,
}

# Title
chart.options.title = {
    "text": "line-timeseries · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold"},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Daily Temperature Readings - 2024",
    "style": {"fontSize": "36px", "color": "#666666"},
}

# X-axis (datetime) - with monthly tick intervals to prevent label overlap
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "36px"}, "margin": 25},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "tickInterval": 30 * 24 * 3600 * 1000,  # Monthly ticks (30 days in ms)
    "dateTimeLabelFormats": {"month": "%b %Y"},
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "36px"}, "margin": 25},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Legend
chart.options.legend = {"enabled": True, "itemStyle": {"fontSize": "32px"}, "margin": 30}

# Tooltip
chart.options.tooltip = {"xDateFormat": "%A, %b %d, %Y", "valueSuffix": " °C", "style": {"fontSize": "28px"}}

# Plot options
chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidth": 6}}}
}

# Add series
series = LineSeries()
series.name = "Temperature"
series.data = data_points
series.color = "#306998"  # Python Blue

chart.add_series(series)

# Export to PNG via Selenium
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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

# Save HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    cdn_html = (
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 600px;"></div>
    <script>"""
        + html_str
        + """</script>
</body>
</html>"""
    )
    f.write(cdn_html)

# Take screenshot with headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Screenshot the chart container element for exact dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
