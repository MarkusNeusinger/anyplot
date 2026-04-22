""" pyplots.ai
area-stacked-percent: 100% Stacked Area Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-30
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Market share evolution over time (2018-2025)
years = ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]

# Market share data for three product categories (raw values that will be normalized)
product_a = [35, 38, 42, 45, 48, 50, 52, 55]  # Growing market leader
product_b = [40, 38, 35, 32, 30, 28, 26, 24]  # Declining legacy product
product_c = [25, 24, 23, 23, 22, 22, 22, 21]  # Stable niche product

# Chart setup
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 300,
    "marginLeft": 180,
    "marginTop": 140,
}

# Title
chart.options.title = {
    "text": "area-stacked-percent \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Product Market Share Evolution (2018-2025)", "style": {"fontSize": "32px"}}

# X-axis configuration
chart.options.x_axis = {
    "categories": years,
    "title": {"text": "Year", "style": {"fontSize": "32px"}},
    "labels": {"style": {"fontSize": "28px"}},
}

# Y-axis configuration for percentage stacking
chart.options.y_axis = {
    "title": {"text": "Market Share (%)", "style": {"fontSize": "32px"}},
    "labels": {"style": {"fontSize": "28px"}, "format": "{value}%"},
    "min": 0,
    "max": 100,
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
    "itemStyle": {"fontSize": "28px"},
    "symbolRadius": 0,
}

# Tooltip configuration
chart.options.tooltip = {
    "pointFormat": '<span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b><br/>',
    "shared": True,
    "style": {"fontSize": "24px"},
}

# Colorblind-safe colors (Python Blue, Python Yellow, Purple)
colors = ["#306998", "#FFD43B", "#9467BD"]

# Add series
series_a = AreaSeries()
series_a.name = "Product A"
series_a.data = product_a
series_a.color = colors[0]
chart.add_series(series_a)

series_b = AreaSeries()
series_b.name = "Product B"
series_b.data = product_b
series_b.color = colors[1]
chart.add_series(series_b)

series_c = AreaSeries()
series_c.name = "Product C"
series_c.data = product_c
series_c.color = colors[2]
chart.add_series(series_c)

# Download Highcharts JS for inline embedding
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
driver.save_screenshot("plot.png")
driver.quit()

# Clean up and save HTML
Path(temp_path).unlink()

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)
