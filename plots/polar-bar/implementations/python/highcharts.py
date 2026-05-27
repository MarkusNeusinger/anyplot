""" anyplot.ai
polar-bar: Polar Bar Chart (Wind Rose)
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
"""

import os
import tempfile
import time
from pathlib import Path

import numpy as np
import requests
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

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Wind direction frequency by speed category
np.random.seed(42)

# 8 compass directions
directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# Wind speed categories (frequency counts for each direction)
# Simulating realistic wind patterns - prevailing westerlies
calm = [3, 2, 2, 1, 2, 3, 5, 4]
light = [8, 5, 6, 3, 4, 7, 12, 10]  # 1-10 mph
moderate = [5, 3, 4, 2, 3, 8, 15, 8]  # 10-20 mph
strong = [2, 1, 2, 1, 1, 4, 8, 5]  # 20+ mph

# Download Highcharts JS modules from jsDelivr CDN
headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11.4.3/highcharts.min.js"
response = requests.get(highcharts_url, timeout=30, headers=headers)
response.raise_for_status()
highcharts_js = response.text

highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@11.4.3/highcharts-more.min.js"
response_more = requests.get(highcharts_more_url, timeout=30, headers=headers)
response_more.raise_for_status()
highcharts_more_js = response_more.text

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "polar": True,
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 250,
}

# Title
chart.options.title = {
    "text": "polar-bar · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Wind Speed Distribution by Direction",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# Pane configuration for polar chart
chart.options.pane = {"size": "70%", "startAngle": 0, "endAngle": 360, "center": ["50%", "50%"]}

# X axis (angular - directions)
chart.options.x_axis = {
    "categories": directions,
    "tickmarkPlacement": "on",
    "lineWidth": 0,
    "labels": {"style": {"fontSize": "22px", "color": INK_SOFT}, "distance": 30},
}

# Y axis (radial - frequency)
chart.options.y_axis = {
    "min": 0,
    "endOnTick": False,
    "showLastLabel": True,
    "title": {"text": "Frequency", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "reversedStacks": False,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "symbolRadius": 0,
    "symbolHeight": 20,
    "symbolWidth": 28,
    "itemMarginBottom": 15,
    "x": -50,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Plot options for stacked column
chart.options.plot_options = {
    "series": {"stacking": "normal", "shadow": False, "groupPadding": 0, "pointPlacement": "on"},
    "column": {"pointPadding": 0, "groupPadding": 0, "borderWidth": 1, "borderColor": PAGE_BG},
}

# Add series with Okabe-Ito colors
series_data = [
    {"name": "Calm (<1 mph)", "data": calm, "color": IMPRINT[0]},
    {"name": "Light (1-10 mph)", "data": light, "color": IMPRINT[1]},
    {"name": "Moderate (10-20 mph)", "data": moderate, "color": IMPRINT[2]},
    {"name": "Strong (>20 mph)", "data": strong, "color": IMPRINT[3]},
]

chart.options.series = series_data

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

# Save theme-suffixed HTML
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
