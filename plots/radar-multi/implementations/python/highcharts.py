""" anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: highcharts unknown | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-07
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - Product comparison across key attributes (4 products, 6 attributes)
categories = [
    "Price (Score)",
    "Quality (Score)",
    "Durability (Score)",
    "Support (Score)",
    "Features (Score)",
    "Ease of Use (Score)",
]

# Product A: Premium option - high quality but expensive
product_a = [25, 95, 90, 85, 80, 70]
# Product B: Budget option - low price but basic
product_b = [95, 45, 40, 50, 35, 85]
# Product C: Balanced option - moderate across all
product_c = [60, 70, 65, 70, 65, 75]
# Product D: Feature-rich but complex
product_d = [45, 85, 80, 75, 100, 40]

# Okabe-Ito palette - first series always #009E73
colors = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for polar/radar - using square format for symmetric visualization
chart.options.chart = {
    "polar": True,
    "width": 3600,
    "height": 3600,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
}

# Title
chart.options.title = {
    "text": "Product Comparison · radar-multi · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK},
}

# X-axis (categories around the radar)
chart.options.x_axis = {
    "categories": categories,
    "tickmarkPlacement": "on",
    "lineWidth": 0,
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis (radial axis)
chart.options.y_axis = {
    "gridLineInterpolation": "polygon",
    "lineWidth": 0,
    "min": 0,
    "max": 100,
    "tickInterval": 20,
    "labels": {"style": {"fontSize": "16px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Pane settings for radar
chart.options.pane = {"size": "75%"}

# Plot options for area series on polar chart
chart.options.plot_options = {
    "series": {"pointPlacement": "on"},
    "area": {"fillOpacity": 0.25, "lineWidth": 3, "marker": {"enabled": True, "radius": 6}},
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "16px", "color": INK_SOFT},
    "symbolWidth": 30,
    "symbolHeight": 15,
}

# Credits
chart.options.credits = {"enabled": False}

# Add series for Product A (first series: Okabe-Ito brand green)
series1 = AreaSeries()
series1.data = product_a
series1.name = "Product A (Premium)"
series1.color = colors[0]
chart.add_series(series1)

# Add series for Product B
series2 = AreaSeries()
series2.data = product_b
series2.name = "Product B (Budget)"
series2.color = colors[1]
chart.add_series(series2)

# Add series for Product C
series3 = AreaSeries()
series3.data = product_c
series3.name = "Product C (Balanced)"
series3.color = colors[2]
chart.add_series(series3)

# Add series for Product D
series4 = AreaSeries()
series4.data = product_d
series4.name = "Product D (Feature-Rich)"
series4.color = colors[3]
chart.add_series(series4)

# Download Highcharts JS and highcharts-more.js (required for polar/radar charts)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
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
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact for the site (both themes)
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
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
