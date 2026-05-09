""" anyplot.ai
line-timeseries: Time Series Line Plot
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-09
"""

import math
import os
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


# Read theme from environment
THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive color palette
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series must be #009E73)
BRAND = "#009E73"

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

# Chart configuration - theme-adaptive background
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "spacingTop": 60,
    "spacingBottom": 100,
    "spacingLeft": 80,
    "spacingRight": 80,
}

# Title - theme-adaptive color
chart.options.title = {
    "text": "line-timeseries · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold", "color": INK},
    "margin": 40,
}

# Subtitle - theme-adaptive color
chart.options.subtitle = {"text": "Daily Temperature Readings - 2024", "style": {"fontSize": "36px", "color": INK_SOFT}}

# X-axis (datetime) - with monthly tick intervals to prevent label overlap
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "36px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "tickInterval": 30 * 24 * 3600 * 1000,  # Monthly ticks (30 days in ms)
    "dateTimeLabelFormats": {"month": "%b %Y"},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Y-axis - theme-adaptive colors
chart.options.y_axis = {
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "36px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend - theme-adaptive styling with improved visibility
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "32px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "margin": 30,
}

# Tooltip - theme-adaptive styling
chart.options.tooltip = {
    "xDateFormat": "%A, %b %d, %Y",
    "valueSuffix": " °C",
    "style": {"fontSize": "28px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 4,
}

# Plot options
chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidth": 6}}}
}

# Add series with Okabe-Ito brand color
series = LineSeries()
series.name = "Temperature"
series.data = data_points
series.color = BRAND  # #009E73 - Okabe-Ito position 1

chart.add_series(series)

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://unpkg.com/highcharts@11/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate chart JS
html_str = chart.to_js_literal()

# Create HTML content with proper theme-adaptive styling
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML version with theme suffix
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    cdn_html = (
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background:"""
        + PAGE_BG
        + """;">
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
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
