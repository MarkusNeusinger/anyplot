""" anyplot.ai
point-basic: Point Estimate Plot
Library: highcharts unknown | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-11
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnRangeSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
BRAND = "#009E73"  # First series - always
CI_COLOR = "#C475FD"  # Second series - confidence interval

# Data - Performance metrics by department with confidence intervals
np.random.seed(42)
categories = ["Marketing", "Engineering", "Sales", "Operations", "Finance", "HR", "Research", "Customer Support"]
estimates = np.array([72, 85, 68, 79, 74, 66, 88, 71])
# Generate asymmetric confidence intervals
lower_errors = np.random.uniform(3, 8, len(categories))
upper_errors = np.random.uniform(3, 8, len(categories))
lower = estimates - lower_errors
upper = estimates + upper_errors

# Create chart with container (CRITICAL for rendering)
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginLeft": 280,
    "marginBottom": 250,
    "marginRight": 100,
    "marginTop": 150,
    "inverted": True,  # Horizontal orientation for reading category labels
}

# Title
chart.options.title = {
    "text": "point-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "normal"},
}

# X-axis (categories - appears on left due to inverted)
chart.options.x_axis = {
    "categories": list(categories),
    "title": {"text": "Department", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis (values - appears on bottom due to inverted)
chart.options.y_axis = {
    "title": {"text": "Performance Score", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 50,
    "max": 100,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "plotLines": [{"value": 75, "color": INK_SOFT, "width": 2, "dashStyle": "Dash", "zIndex": 5}],
}

# Legend - positioned closer to plot
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "y": 60,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Error bar series (confidence intervals) using columnrange with endpoint caps
error_data = []
for i in range(len(categories)):
    error_data.append({"x": i, "low": float(lower[i]), "high": float(upper[i])})

error_series = ColumnRangeSeries()
error_series.name = "95% CI"
error_series.data = error_data
error_series.color = CI_COLOR
error_series.border_width = 2
error_series.point_width = 8

chart.add_series(error_series)

# Point estimate series (scatter points)
point_data = []
for i in range(len(categories)):
    point_data.append({"x": i, "y": float(estimates[i])})

point_series = ScatterSeries()
point_series.name = "Point Estimate"
point_series.data = point_data
point_series.color = BRAND
point_series.marker = {"radius": 10, "symbol": "circle", "lineWidth": 2, "lineColor": BRAND, "fillColor": BRAND}

chart.add_series(point_series)

# Plot options with endpoint caps on columnrange
chart.options.plot_options = {
    "series": {"animation": False},
    "scatter": {"marker": {"radius": 10, "states": {"hover": {"enabled": False}}}},
    "columnrange": {"groupPadding": 0, "pointPadding": 0, "pointPlacement": "on"},
}

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download highcharts-more.js for columnrange
highcharts_more_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts-more.js"
req = urllib.request.Request(
    highcharts_more_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with INLINE scripts
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

# Write HTML for interactive version
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
