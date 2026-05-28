""" anyplot.ai
area-stacked: Stacked Area Chart
Library: highcharts unknown | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-07
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette: first series always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Monthly revenue by product category (in thousands $) over 2 years
months = [
    "Jan 2023",
    "Feb 2023",
    "Mar 2023",
    "Apr 2023",
    "May 2023",
    "Jun 2023",
    "Jul 2023",
    "Aug 2023",
    "Sep 2023",
    "Oct 2023",
    "Nov 2023",
    "Dec 2023",
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
    "Nov 2024",
    "Dec 2024",
]

# Revenue data by category (ordered by average size)
electronics = [
    120,
    135,
    145,
    160,
    175,
    190,
    210,
    225,
    195,
    180,
    240,
    280,
    130,
    145,
    155,
    175,
    195,
    210,
    235,
    250,
    215,
    195,
    265,
    310,
]
software = [
    80,
    85,
    95,
    105,
    115,
    120,
    125,
    130,
    135,
    140,
    150,
    165,
    90,
    95,
    105,
    115,
    130,
    140,
    150,
    160,
    165,
    170,
    185,
    200,
]
services = [45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 110, 50, 55, 60, 70, 75, 85, 90, 100, 105, 115, 125, 140]
accessories = [25, 28, 32, 35, 40, 45, 48, 52, 48, 45, 55, 70, 28, 32, 36, 42, 48, 52, 58, 62, 55, 52, 65, 85]

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 250,
    "spacingBottom": 100,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
}

# Title
chart.options.title = {
    "text": "area-stacked · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "Monthly Revenue by Product Category (2023-2024)",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis
chart.options.x_axis = {
    "categories": months,
    "title": {"text": "Month", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "tickmarkPlacement": "on",
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Revenue ($ thousands)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

# Legend with theme-adaptive background
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "x": -50,
    "y": 100,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 15,
}

# Plot options for stacked area
chart.options.plot_options = {
    "area": {
        "stacking": "normal",
        "lineWidth": 3,
        "marker": {"enabled": False, "radius": 6, "states": {"hover": {"enabled": True}}},
        "fillOpacity": 0.75,
    }
}

# Tooltip
chart.options.tooltip = {
    "shared": True,
    "style": {"fontSize": "18px", "color": INK},
    "headerFormat": '<span style="font-size: 20px; color: {0}">{point.key}</span><br/>',
    "pointFormat": '<span style="color:{series.color}">●</span> {series.name}: <b>${point.y}K</b><br/>',
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
}

# Set Okabe-Ito colors
chart.options.colors = IMPRINT

# Add series (ordered by average size, largest first per spec)
series_data = [
    ("Electronics", electronics),
    ("Software", software),
    ("Services", services),
    ("Accessories", accessories),
]

for name, data in series_data:
    series = AreaSeries()
    series.name = name
    series.data = data
    chart.add_series(series)

# Get Highcharts JS from npm package
# Install highcharts globally if needed
subprocess.run(["npm", "install", "--location=global", "--silent", "highcharts"], capture_output=True)

# Read highcharts.js from node_modules
highcharts_path = "/usr/local/lib/node_modules/highcharts/highcharts.js"
with open(highcharts_path, "r", encoding="utf-8") as f:
    highcharts_js = f.read()

# Generate HTML with inline scripts
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

# Save HTML artifact for the site (both themes)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
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

# Clean up temp file
Path(temp_path).unlink()
