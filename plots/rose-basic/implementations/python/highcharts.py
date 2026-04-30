"""anyplot.ai
rose-basic: Basic Rose Chart
Library: highcharts unknown | Python 3.13.13
Quality: 85/100 | Updated: 2026-04-30
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Monthly rainfall in mm (UK-like temperate oceanic climate)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [78, 52, 65, 45, 38, 25, 18, 22, 42, 68, 85, 92]

# Value-proportional color gradient: light mint (low) → brand green (peak)
# Encodes rainfall intensity visually — wet months appear darker and more saturated
_lo = (200, 232, 222)  # #C8E8DE light mint base
_hi = (0, 158, 115)  # #009E73 brand green
_mn, _mx = min(rainfall), max(rainfall)
colors = [
    "#{:02X}{:02X}{:02X}".format(
        int(_lo[0] + (v - _mn) / (_mx - _mn) * (_hi[0] - _lo[0])),
        int(_lo[1] + (v - _mn) / (_mx - _mn) * (_hi[1] - _lo[1])),
        int(_lo[2] + (v - _mn) / (_mx - _mn) * (_hi[2] - _lo[2])),
    )
    for v in rainfall
]

# Create chart with polar/rose configuration
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Square canvas — optimal geometry for a circular rose chart
chart.options.chart = {
    "polar": True,
    "type": "column",
    "width": 3600,
    "height": 3600,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
}

# Title
chart.options.title = {
    "text": "rose-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": INK},
}

# Subtitle for context
chart.options.subtitle = {"text": "Monthly Rainfall (mm)", "style": {"fontSize": "32px", "color": INK_SOFT}}

# X-axis (categories around the circle)
chart.options.x_axis = {
    "categories": months,
    "tickmarkPlacement": "on",
    "lineWidth": 0,
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}},
    "gridLineColor": GRID,
}

# Y-axis (radial — values extend from center)
chart.options.y_axis = {
    "min": 0,
    "gridLineInterpolation": "polygon",
    "lineWidth": 0,
    "labels": {"format": "{value} mm", "style": {"fontSize": "22px", "color": INK_SOFT}},
    "title": {"text": "Rainfall (mm)", "style": {"fontSize": "28px", "color": INK}},
    "gridLineColor": GRID,
}

# Pane — startAngle 0 places Jan at 12 o'clock; larger pane fills square canvas
chart.options.pane = {"size": "88%", "startAngle": 0}

# Plot options for the rose/polar column
chart.options.plot_options = {
    "column": {"pointPadding": 0, "groupPadding": 0, "borderWidth": 2, "borderColor": PAGE_BG},
    "series": {
        "dataLabels": {
            "enabled": True,
            "format": "{y}",
            "style": {"fontSize": "26px", "fontWeight": "normal", "color": INK_SOFT},
        }
    },
}

# Rich tooltip using Highcharts pointFormat — highlights the per-point color swatch
chart.options.tooltip = {
    "headerFormat": "<span style='font-size:24px'><b>{point.key}</b></span><br/>",
    "pointFormat": "<span style='color:{point.color}'>●</span> Rainfall: <b>{point.y} mm</b>",
    "backgroundColor": ELEVATED_BG,
    "style": {"color": INK, "fontSize": "22px"},
    "borderColor": INK_SOFT,
}

# Disable legend — redundant for a single-series chart
chart.options.legend = {"enabled": False}

# Series with per-point value-proportional colors (colorByPoint via data objects)
series = ColumnSeries()
series.name = "Rainfall"
series.data = [{"y": v, "color": c} for v, c in zip(rainfall, colors, strict=True)]

chart.add_series(series)

# Download Highcharts JS and Highcharts More (required for polar charts)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts-more.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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

# Save HTML artifact for the site
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for the PNG artifact
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
