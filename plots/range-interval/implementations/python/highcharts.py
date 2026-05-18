""" anyplot.ai
range-interval: Range Interval Chart
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-18
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnRangeSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data: Monthly temperature ranges for a temperate city
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Realistic temperature pattern (Northern Hemisphere temperate climate)
base_lows = [-2, -1, 3, 7, 12, 16, 18, 17, 13, 8, 3, -1]
base_highs = [5, 7, 12, 17, 22, 26, 29, 28, 23, 16, 10, 6]

# Add slight variation
min_temps = [low + np.random.uniform(-1, 1) for low in base_lows]
max_temps = [high + np.random.uniform(-1, 1) for high in base_highs]

# Create chart with container specified
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 canvas
chart.options.chart = {
    "type": "columnrange",
    "inverted": False,
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginLeft": 150,
    "marginTop": 100,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
}

# Title
chart.options.title = {
    "text": "range-interval · python · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
}

# Subtitle for context
chart.options.subtitle = {"text": "Monthly Temperature Ranges (°C)", "style": {"fontSize": "22px", "color": INK_SOFT}}

# X-axis (categories)
chart.options.x_axis = {
    "categories": months,
    "title": {"text": "Month", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "y": 40},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "crosshair": False,
}

# Y-axis (temperature values)
chart.options.y_axis = {
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Plot options for column range
chart.options.plot_options = {
    "columnrange": {
        "borderRadius": 3,
        "dataLabels": {
            "enabled": True,
            "format": "{y}°C",
            "style": {"fontSize": "20px", "fontWeight": "normal", "textOutline": "none", "color": INK_SOFT},
        },
    }
}

# Legend configuration - positioned at bottom for better integration
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "verticalAlign": "bottom",
    "align": "center",
    "layout": "horizontal",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Tooltip configuration
chart.options.tooltip = {
    "valueSuffix": "°C",
    "style": {"fontSize": "18px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
}

# Colors
chart.options.colors = [BRAND]

# Create the column range series
series = ColumnRangeSeries()
series.name = "Temperature Range"
series.color = BRAND

# Data format for columnrange: [[low, high], [low, high], ...]
series.data = [[round(min_temps[i], 1), round(max_temps[i], 1)] for i in range(len(months))]

chart.add_series(series)

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
req = urllib.request.Request(
    highcharts_url,
    headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://highcharts.com/",
        "Accept": "*/*",
    },
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download highcharts-more.js for columnrange support
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
req_more = urllib.request.Request(
    highcharts_more_url,
    headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://highcharts.com/",
        "Accept": "*/*",
    },
)
with urllib.request.urlopen(req_more, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG artifact
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
