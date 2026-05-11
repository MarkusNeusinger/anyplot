""" anyplot.ai
histogram-cumulative: Cumulative Histogram
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
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Student test scores (realistic educational context)
np.random.seed(42)
scores = np.concatenate(
    [
        np.random.normal(65, 10, 150),  # Average performers
        np.random.normal(85, 5, 80),  # High performers
        np.random.normal(45, 8, 50),  # Struggling students
    ]
)
scores = np.clip(scores, 0, 100)  # Clip to valid score range

# Calculate cumulative histogram data
n_bins = 20
counts, bin_edges = np.histogram(scores, bins=n_bins, range=(0, 100))
cumulative_counts = np.cumsum(counts)
cumulative_proportion = cumulative_counts / len(scores) * 100  # Percentage

# Prepare data for Highcharts area/step chart
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
data_points = [[float(x), float(y)] for x, y in zip(bin_centers, cumulative_proportion, strict=True)]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 250,
    "marginLeft": 200,
    "marginRight": 100,
    "marginTop": 180,
}

# Title
chart.options.title = {
    "text": "histogram-cumulative · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "normal"},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Test Score", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Cumulative Percentage (%)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "{value}%"},
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"color": INK_SOFT, "fontSize": "16px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Plot options for step-like appearance
chart.options.plot_options = {
    "area": {
        "step": "center",
        "marker": {"enabled": True, "radius": 8, "fillColor": BRAND, "lineColor": BRAND, "lineWidth": 2},
        "lineWidth": 3,
        "color": BRAND,
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, "rgba(0, 158, 115, 0.3)"], [1, "rgba(0, 158, 115, 0.05)"]],
        },
    }
}

# Credits
chart.options.credits = {"enabled": False}

# Add series
series = AreaSeries()
series.data = data_points
series.name = "Cumulative Distribution"
chart.add_series(series)

# Export to PNG via Selenium
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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
