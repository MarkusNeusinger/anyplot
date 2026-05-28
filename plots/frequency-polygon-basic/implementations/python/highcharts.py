""" anyplot.ai
frequency-polygon-basic: Frequency Polygon for Distribution Comparison
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-17
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme configuration
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD"]

# Data - Test scores for three different classes
np.random.seed(42)
# Class A: Normal distribution, average performance
class_a = np.random.normal(loc=72, scale=12, size=200)
# Class B: Higher average, tighter spread
class_b = np.random.normal(loc=80, scale=8, size=200)
# Class C: Bimodal - mix of high and low performers
class_c = np.concatenate([np.random.normal(loc=55, scale=8, size=100), np.random.normal(loc=85, scale=6, size=100)])

# Clip to valid score range
class_a = np.clip(class_a, 0, 100)
class_b = np.clip(class_b, 0, 100)
class_c = np.clip(class_c, 0, 100)

# Calculate histogram bin edges (same bins for all groups)
bins = np.linspace(0, 100, 21)  # 20 bins
bin_centers = (bins[:-1] + bins[1:]) / 2

# Calculate frequency (count) for each class
freq_a, _ = np.histogram(class_a, bins=bins)
freq_b, _ = np.histogram(class_b, bins=bins)
freq_c, _ = np.histogram(class_c, bins=bins)

# Extend lines to zero at both ends to close the polygon shape
extended_centers = np.concatenate([[bins[0]], bin_centers, [bins[-1]]])
freq_a_extended = np.concatenate([[0], freq_a, [0]])
freq_b_extended = np.concatenate([[0], freq_b, [0]])
freq_c_extended = np.concatenate([[0], freq_c, [0]])

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "spline",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 180,
    "marginLeft": 140,
    "marginRight": 100,
    "marginTop": 120,
}

# Title
chart.options.title = {
    "text": "frequency-polygon-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# X-axis (score ranges)
chart.options.x_axis = {
    "title": {"text": "Test Score (0-100)", "style": {"fontSize": "22px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "y": 35},
    "tickInterval": 10,
    "min": 0,
    "max": 100,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Y-axis (frequency)
chart.options.y_axis = {
    "title": {"text": "Frequency (count)", "style": {"fontSize": "22px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "16px", "color": INK_SOFT},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 80,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Plot options for spline (frequency polygon)
chart.options.plot_options = {
    "spline": {"fillOpacity": 0.2, "lineWidth": 5, "marker": {"enabled": True, "radius": 8, "symbol": "circle"}}
}

# Create series for each class using Okabe-Ito palette
series_a = SplineSeries()
series_a.name = "Class A (Avg: 72)"
series_a.data = [[float(x), int(y)] for x, y in zip(extended_centers, freq_a_extended, strict=True)]
series_a.color = IMPRINT[0]  # #009E73 - brand green
series_a.fill_color = IMPRINT[0]
series_a.marker = {"fillColor": IMPRINT[0], "lineWidth": 2, "lineColor": PAGE_BG}

series_b = SplineSeries()
series_b.name = "Class B (Avg: 80)"
series_b.data = [[float(x), int(y)] for x, y in zip(extended_centers, freq_b_extended, strict=True)]
series_b.color = IMPRINT[1]  # #C475FD - vermillion
series_b.fill_color = IMPRINT[1]
series_b.marker = {"fillColor": IMPRINT[1], "lineWidth": 2, "lineColor": PAGE_BG}

series_c = SplineSeries()
series_c.name = "Class C (Bimodal)"
series_c.data = [[float(x), int(y)] for x, y in zip(extended_centers, freq_c_extended, strict=True)]
series_c.color = IMPRINT[2]  # #4467A3 - blue
series_c.fill_color = IMPRINT[2]
series_c.marker = {"fillColor": IMPRINT[2], "lineWidth": 2, "lineColor": PAGE_BG}

# Add series to chart
chart.add_series(series_a)
chart.add_series(series_b)
chart.add_series(series_c)

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS (required for headless Chrome)
highcharts_urls = ["https://code.highcharts.com/highcharts.js", "https://unpkg.com/highcharts@latest/highcharts.js"]
highcharts_js = None
for url in highcharts_urls:
    for attempt in range(2):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
                break
        except Exception:
            if attempt == 1:
                break
            time.sleep(1)
    if highcharts_js:
        break

if not highcharts_js:
    raise RuntimeError("Failed to download Highcharts from any source. Check network connectivity.")

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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file

# Also save HTML for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    # Use CDN for the standalone HTML file (works in browsers)
    interactive_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>frequency-polygon-basic - highcharts - anyplot.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(interactive_html)
