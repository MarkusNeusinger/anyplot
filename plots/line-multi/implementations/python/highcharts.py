""" anyplot.ai
line-multi: Multi-Line Comparison Plot
Library: highcharts unknown | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-06
"""

import os
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


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Monthly sales for 4 product lines over 12 months
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Electronics - steady growth with seasonal dip
electronics = [120, 135, 142, 138, 155, 165, 158, 172, 185, 210, 245, 280]

# Clothing - seasonal pattern with summer and winter peaks
clothing = [95, 88, 82, 78, 92, 115, 125, 118, 95, 88, 110, 145]

# Home & Garden - spring/summer peak
home_garden = [65, 72, 95, 125, 145, 155, 148, 135, 110, 85, 70, 68]

# Sports Equipment - gradual increase
sports = [45, 48, 55, 68, 85, 92, 105, 98, 88, 75, 65, 58]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 px
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    "spacingBottom": 100,
    "spacingTop": 50,
}

# Title
chart.options.title = {
    "text": "line-multi · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# Subtitle
chart.options.subtitle = {
    "text": "Monthly Sales by Product Category (thousands USD)",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis configuration
chart.options.x_axis = {
    "categories": months,
    "title": {"text": "Month", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Sales (thousands USD)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "min": 0,
}

# Legend configuration - position at top right
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "top",
    "x": -50,
    "y": 150,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "backgroundColor": ELEVATED_BG,
    "padding": 20,
    "itemMarginTop": 10,
    "itemMarginBottom": 10,
}

# Plot options for line styling
chart.options.plot_options = {
    "line": {"lineWidth": 3, "marker": {"enabled": True, "radius": 8, "lineWidth": 2, "lineColor": PAGE_BG}}
}

# Set colors for the chart
chart.options.colors = IMPRINT

# Add series - Electronics
series1 = LineSeries()
series1.name = "Electronics"
series1.data = electronics
series1.color = IMPRINT[0]
chart.add_series(series1)

# Add series - Clothing
series2 = LineSeries()
series2.name = "Clothing"
series2.data = clothing
series2.color = IMPRINT[1]
chart.add_series(series2)

# Add series - Home & Garden
series3 = LineSeries()
series3.name = "Home & Garden"
series3.data = home_garden
series3.color = IMPRINT[2]
chart.add_series(series3)

# Add series - Sports Equipment
series4 = LineSeries()
series4.name = "Sports Equipment"
series4.data = sports
series4.color = IMPRINT[3]
chart.add_series(series4)

# Download Highcharts JS for inline embedding
highcharts_url = "https://unpkg.com/highcharts"
headers = {"User-Agent": "Mozilla/5.0"}
req = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
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

# Save HTML version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Create PNG via headless Chrome
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
