""" anyplot.ai
histogram-stepwise: Step Histogram
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Created: 2026-05-12
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data: Test scores (continuous)
np.random.seed(42)
test_scores = np.concatenate([np.random.normal(72, 8, 150), np.random.normal(85, 6, 100)])
test_scores = np.clip(test_scores, 0, 100)

# Create histogram with numpy
counts, bin_edges = np.histogram(test_scores, bins=20)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Convert to step function: create continuous stepped line
# Start from first bin edge at height 0
step_x = [float(bin_edges[0])]
step_y = [0]

# For each bin, create horizontal segment at count level, then vertical to next
for i in range(len(counts)):
    bin_left = float(bin_edges[i])
    bin_right = float(bin_edges[i + 1])
    count = int(counts[i])

    # Horizontal segment from left edge to right edge at count height
    if i == 0 or step_y[-1] != count:
        # Vertical segment to reach this bin's height (if different from previous)
        step_x.append(step_x[-1])
        step_y.append(count)

    # Horizontal segment across the bin
    step_x.append(bin_right)
    step_y.append(count)

# Return to baseline at the end
if step_y[-1] != 0:
    step_x.append(step_x[-1])
    step_y.append(0)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Configure chart
chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
}

# Title
chart.options.title = {
    "text": "histogram-stepwise · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "normal"},
}

# Axes
chart.options.x_axis = {
    "title": {"text": "Test Score", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "type": "linear",
}
chart.options.y_axis = {
    "title": {"text": "Frequency", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "startFromZero": True,
}

# Series: step histogram as line
series = LineSeries()
series.name = "Distribution"
series.data = list(zip(step_x, step_y, strict=False))
series.color = BRAND
series.line_width = 3
series.enable_mouse_tracking = False

chart.add_series(series)

# Legend (minimal)
chart.options.legend = {"enabled": False}

# Plot options for line
chart.options.plot_options = {"line": {"lineWidth": 3, "marker": {"enabled": False}}}

# Download Highcharts JS from jsDelivr CDN
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Generate PNG via Selenium
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
