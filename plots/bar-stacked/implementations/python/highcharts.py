""" anyplot.ai
bar-stacked: Stacked Bar Chart
Library: highcharts unknown | Python 3.13.13
Quality: 98/100 | Updated: 2026-05-09
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data: Monthly energy consumption by source (in MWh)
categories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
components = {
    "Solar": [120, 150, 210, 280, 350, 420],
    "Natural Gas": [380, 320, 290, 340, 280, 310],
    "Nuclear": [450, 445, 455, 448, 452, 447],
    "Coal": [350, 310, 270, 220, 180, 140],
}

# Okabe-Ito palette: first series is always #009E73
colors = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 250,
    "marginTop": 120,
    "marginLeft": 200,
    "spacingBottom": 80,
}

# Title
chart.options.title = {
    "text": "bar-stacked · highcharts · anyplot.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": INK},
}

# Subtitle
chart.options.subtitle = {
    "text": "Monthly Energy Consumption by Source",
    "style": {"fontSize": "32px", "color": INK_SOFT},
}

# X-axis
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Month", "style": {"fontSize": "32px", "color": INK}},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Energy (MWh)", "style": {"fontSize": "32px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "stackLabels": {"enabled": True, "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK}},
}

# Legend - positioned above to avoid conflict with X-axis
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal", "color": INK_SOFT},
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "top",
    "y": 60,
    "symbolRadius": 0,
    "symbolHeight": 24,
    "symbolWidth": 32,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Plot options for stacking
chart.options.plot_options = {
    "column": {
        "stacking": "normal",
        "borderWidth": 2,
        "borderColor": PAGE_BG,
        "dataLabels": {
            "enabled": True,
            "style": {"fontSize": "26px", "fontWeight": "normal", "color": INK},
            "format": "{y}",
        },
    }
}

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "24px", "color": INK},
    "headerFormat": "<b>{point.x}</b><br/>",
    "pointFormat": "{series.name}: {point.y} MWh<br/>Total: {point.stackTotal} MWh",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 4,
}

# Add series for each component
for i, (component_name, values) in enumerate(components.items()):
    series = ColumnSeries()
    series.name = component_name
    series.data = values
    series.color = colors[i % len(colors)]
    chart.add_series(series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline script
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML file
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Create temp file for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Screenshot using Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Screenshot the container element
container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
