""" anyplot.ai
step-basic: Basic Step Plot
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-04-30
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

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
BRAND = "#009E73"

# Data - Monthly cumulative sales (thousands of dollars)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
cumulative_sales = [45, 92, 156, 198, 267, 312, 398, 445, 523, 612, 695, 780]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 250,
    "marginLeft": 200,
}

# Title
chart.options.title = {
    "text": "step-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold", "color": INK},
}

# X-axis
chart.options.x_axis = {
    "categories": months,
    "title": {"text": "Month", "style": {"fontSize": "48px", "color": INK}},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Cumulative Sales ($K)", "style": {"fontSize": "48px", "color": INK}},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Plot options — step line with markers
chart.options.plot_options = {
    "line": {"step": "left", "lineWidth": 6, "marker": {"enabled": True, "radius": 12, "symbol": "circle"}}
}

# Legend disabled — single series
chart.options.legend = {"enabled": False}

# Series
series = LineSeries()
series.name = "Cumulative Sales"
series.data = cumulative_sales
series.color = BRAND

chart.add_series(series)

# Download Highcharts JS for inline embedding (headless Chrome cannot load CDN)
cdn_urls = ["https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js", "https://code.highcharts.com/highcharts.js"]
highcharts_js = None
for url in cdn_urls:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
        break
    except Exception:
        continue
if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts JS from all CDN sources")

# Build HTML with inline script
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

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
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
