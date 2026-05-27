""" anyplot.ai
line-styled: Styled Line Plot
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-12
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
BRAND = "#009E73"  # Okabe-Ito position 1
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Monthly temperature data for 4 cities
np.random.seed(42)
months = list(range(1, 13))
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Realistic temperature patterns (°C)
base_pattern = np.array([5, 7, 12, 16, 21, 25, 28, 27, 23, 17, 11, 6])
berlin = base_pattern + np.random.randn(12) * 1.5
oslo = base_pattern - 8 + np.random.randn(12) * 1.5
madrid = base_pattern + 5 + np.random.randn(12) * 1.5
edinburgh = base_pattern - 3 + np.random.randn(12) * 1.5

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginLeft": 180,
    "marginRight": 150,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "line-styled · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
}

# X-axis (categories)
chart.options.x_axis = {
    "categories": month_names,
    "title": {"text": "Month", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 0,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolWidth": 80,
    "symbolHeight": 24,
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "middle",
    "x": -50,
}

# Plot options for lines
chart.options.plot_options = {"line": {"lineWidth": 6, "marker": {"enabled": True, "radius": 10}}}

# Add series with different line styles using Okabe-Ito colors
# Series 1 - Solid (brand green)
series1 = LineSeries()
series1.name = "Madrid"
series1.data = [round(float(v), 1) for v in madrid]
series1.color = IMPRINT[0]
series1.dash_style = "Solid"
chart.add_series(series1)

# Series 2 - Dash (vermillion)
series2 = LineSeries()
series2.name = "Berlin"
series2.data = [round(float(v), 1) for v in berlin]
series2.color = IMPRINT[1]
series2.dash_style = "Dash"
chart.add_series(series2)

# Series 3 - Dot (blue)
series3 = LineSeries()
series3.name = "Edinburgh"
series3.data = [round(float(v), 1) for v in edinburgh]
series3.color = IMPRINT[2]
series3.dash_style = "Dot"
chart.add_series(series3)

# Series 4 - DashDot (reddish purple)
series4 = LineSeries()
series4.name = "Oslo"
series4.data = [round(float(v), 1) for v in oslo]
series4.color = IMPRINT[3]
series4.dash_style = "DashDot"
chart.add_series(series4)

# Download Highcharts JS
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
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

# Save HTML artifact for the site
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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
