""" anyplot.ai
count-basic: Basic Count Plot
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-07
"""

import os
import tempfile
import time
from collections import Counter
from pathlib import Path

import requests
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data - Survey responses (raw categorical data to be counted)
responses = [
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Satisfied",
    "Very Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Neutral",
    "Very Satisfied",
    "Satisfied",
    "Very Dissatisfied",
    "Satisfied",
    "Dissatisfied",
    "Neutral",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
]

# Count occurrences
counts = Counter(responses)

# Sort by frequency (descending)
sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
categories = [item[0] for item in sorted_counts]
values = [item[1] for item in sorted_counts]

# Create chart with container specified (CRITICAL for PNG export)
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 px
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 280,
    "marginTop": 120,
}

# Title
chart.options.title = {"text": "count-basic · highcharts · anyplot.ai", "style": {"fontSize": "28px", "color": INK}}

# X-axis with categories
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Response Category", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Number of Responses", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

# Legend disabled (single series)
chart.options.legend = {"enabled": False}

# Plot options with data labels and Highcharts features
chart.options.plot_options = {
    "column": {
        "dataLabels": {
            "enabled": True,
            "format": "{y}",
            "style": {"fontSize": "20px", "color": INK, "fontWeight": "bold"},
        },
        "borderRadius": 4,
        "borderWidth": 0,
        "tooltip": {"headerFormat": "<b>{point.key}</b><br>", "pointFormat": "{y} responses"},
    }
}

# Create series with Okabe-Ito brand green
series = ColumnSeries()
series.data = values
series.name = "Count"
series.color = BRAND

chart.add_series(series)

# Download Highcharts JS for inline embedding (with CDN fallback)
highcharts_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
    "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.0.0/highcharts.min.js",
]

highcharts_js = None
for highcharts_url in highcharts_urls:
    try:
        response = requests.get(highcharts_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        highcharts_js = response.text
        break
    except Exception:
        continue

if highcharts_js is None:
    raise RuntimeError("Could not download Highcharts from any CDN")

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

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML file with theme suffix
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Selenium headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
