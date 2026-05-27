""" anyplot.ai
area-stacked-percent: 100% Stacked Area Chart
Library: highcharts unknown | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-12
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


# Theme-adaptive tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Market share evolution over time (2018-2025)
years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]

# Market share data for three product categories (raw values that will be normalized)
product_a = [35, 38, 42, 45, 48, 50, 52, 55]
product_b = [40, 38, 35, 32, 30, 28, 26, 24]
product_c = [25, 24, 23, 23, 22, 22, 22, 21]

# Chart setup
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 300,
    "marginLeft": 180,
    "marginTop": 140,
}

# Title
chart.options.title = {
    "text": "area-stacked-percent · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# Subtitle
chart.options.subtitle = {
    "text": "Product Market Share Evolution (2018-2025)",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis configuration
chart.options.x_axis = {
    "categories": years,
    "title": {"text": "Year", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

# Y-axis configuration for percentage stacking
chart.options.y_axis = {
    "title": {"text": "Market Share (%)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "{value}%"},
    "min": 0,
    "max": 100,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

# Plot options for 100% stacking
chart.options.plot_options = {
    "area": {"stacking": "percent", "lineWidth": 2, "marker": {"enabled": True, "radius": 8}, "fillOpacity": 0.7}
}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "y": -20,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "symbolRadius": 6,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Tooltip configuration
chart.options.tooltip = {
    "pointFormat": '<span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b><br/>',
    "shared": True,
    "style": {"fontSize": "18px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
}

# Color palette - Okabe-Ito
chart.options.colors = IMPRINT

# Add series
series_a = AreaSeries()
series_a.name = "Product A"
series_a.data = product_a
series_a.color = IMPRINT[0]
chart.add_series(series_a)

series_b = AreaSeries()
series_b.name = "Product B"
series_b.data = product_b
series_b.color = IMPRINT[1]
chart.add_series(series_b)

series_c = AreaSeries()
series_c.name = "Product C"
series_c.data = product_c
series_c.color = IMPRINT[2]
chart.add_series(series_c)

# Download Highcharts JS for inline embedding
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
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

# Chrome options for headless screenshot
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
