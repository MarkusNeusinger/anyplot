""" anyplot.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: highcharts unknown | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-08
"""

import os
import tempfile
import time
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    pass

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette - first series is always #009E73
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data: Market share by quarter for different companies
categories = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025"]
series_data = {
    "TechCorp": [35, 33, 30, 28, 26],
    "DataFlow": [25, 27, 28, 30, 32],
    "CloudPeak": [20, 21, 23, 24, 25],
    "NetBase": [12, 12, 12, 11, 10],
    "Others": [8, 7, 7, 7, 7],
}

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {"type": "column", "width": 4800, "height": 2700, "backgroundColor": PAGE_BG, "marginBottom": 250}

# Title
chart.options.title = {
    "text": "bar-stacked-percent · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "medium", "color": INK},
}

# Subtitle
chart.options.subtitle = {"text": "Market Share by Quarter", "style": {"fontSize": "20px", "color": INK_SOFT}}

# X-axis (categories)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Quarter", "style": {"fontSize": "22px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis (percentage) - reduced tick marks for cleaner appearance
chart.options.y_axis = {
    "min": 0,
    "max": 100,
    "title": {"text": "Market Share (%)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "{value}%"},
    "tickInterval": 20,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Plot options for 100% stacked column
chart.options.plot_options = {
    "column": {
        "stacking": "percent",
        "borderWidth": 1,
        "borderColor": PAGE_BG,
        "dataLabels": {
            "enabled": True,
            "format": "{point.percentage:.1f}%",
            "style": {"fontSize": "18px", "fontWeight": "normal", "textOutline": "none", "color": "#FFFFFF"},
        },
    }
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolRadius": 0,
    "symbolHeight": 20,
    "symbolWidth": 40,
    "itemDistance": 50,
    "margin": 20,
    "y": -60,
}

# Tooltip
chart.options.tooltip = {
    "pointFormat": '<span style="color:{point.color}">●</span> {series.name}: <b>{point.percentage:.1f}%</b> ({point.y})<br/>',
    "shared": False,
    "style": {"fontSize": "18px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
}

# Add series with Okabe-Ito colors
for i, (name, data) in enumerate(series_data.items()):
    series = ColumnSeries()
    series.name = name
    series.data = data
    series.color = IMPRINT[i % len(IMPRINT)]
    chart.add_series(series)

# Download Highcharts JS (required for headless Chrome)
# Try multiple CDN sources for resilience
highcharts_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js",
    "https://unpkg.com/highcharts@11/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
]

highcharts_js = None
for url in highcharts_urls:
    try:
        session = requests.Session()
        retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[403, 429, 500, 502])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        response = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        response.raise_for_status()
        highcharts_js = response.text
        break
    except Exception:
        continue

if highcharts_js is None:
    raise RuntimeError("Could not download Highcharts JS from any CDN")

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

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

# Take screenshot
driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
