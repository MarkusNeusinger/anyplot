""" anyplot.ai
polar-line: Polar Line Plot
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-12
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
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
IMPRINT = ["#009E73", "#C475FD"]

# Data - Monthly temperature pattern (cyclical, degrees around year)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Simulating monthly average temperatures for two cities
city_a = [2, 4, 9, 14, 19, 23, 26, 25, 20, 14, 8, 3]  # Continental climate
city_b = [8, 9, 11, 13, 16, 19, 21, 21, 19, 15, 11, 9]  # Oceanic climate

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for polar line
chart.options.chart = {"polar": True, "width": 3600, "height": 3600, "backgroundColor": PAGE_BG, "spacingBottom": 80}

# Title
chart.options.title = {
    "text": "polar-line · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Monthly Average Temperature Patterns",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis (angular axis - categories)
chart.options.x_axis = {
    "categories": months,
    "tickmarkPlacement": "on",
    "lineWidth": 0,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
}

# Y-axis (radial axis)
chart.options.y_axis = {
    "gridLineInterpolation": "polygon",
    "lineWidth": 0,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "min": 0,
    "max": 30,
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
}

# Plot options for line series
chart.options.plot_options = {"series": {"lineWidth": 3, "marker": {"enabled": True, "radius": 8}}}

# Legend - positioned closer to chart
chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolRadius": 6,
    "itemMarginTop": 10,
    "y": 10,
}

# Add series data with Okabe-Ito colors
chart.options.series = [
    {"type": "line", "name": "Continental City", "data": city_a, "color": IMPRINT[0], "marker": {"symbol": "circle"}},
    {"type": "line", "name": "Oceanic City", "data": city_b, "color": IMPRINT[1], "marker": {"symbol": "diamond"}},
]

# Download Highcharts JS and Highcharts More for polar charts
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts-more.js"

req_hc = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req_hc, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req_hc_more = urllib.request.Request(
    highcharts_more_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req_hc_more, timeout=30) as response:
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
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
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
chrome_options.add_argument("--window-size=3600,3800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Save HTML for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

Path(temp_path).unlink()
