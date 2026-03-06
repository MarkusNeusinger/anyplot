""" pyplots.ai
heatmap-stripes-climate: Climate Warming Stripes
Library: highcharts unknown | Python 3.14.3
Quality: 83/100 | Created: 2026-03-06
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - synthetic global temperature anomalies (1850-2024) relative to 1961-1990 baseline
np.random.seed(42)
years = np.arange(1850, 2025)
n_years = len(years)

# Build a realistic warming trend: slight cooling trend until ~1910, flat until ~1970, then accelerating warming
base_trend = np.piecewise(
    years.astype(float),
    [years < 1910, (years >= 1910) & (years < 1970), years >= 1970],
    [
        lambda y: -0.3 + (y - 1850) * (-0.002),
        lambda y: -0.15 + (y - 1910) * 0.002,
        lambda y: -0.03 + (y - 1970) * 0.022,
    ],
)
noise = np.random.normal(0, 0.08, n_years)
anomalies = base_trend + noise

# Color mapping: blue-to-red diverging, symmetric around 0
vmin = -max(abs(anomalies.min()), abs(anomalies.max()))
vmax = -vmin


def anomaly_to_color(val):
    t = (val - vmin) / (vmax - vmin)
    t = max(0.0, min(1.0, t))
    # Blue (#08306b) -> White (#ffffff) -> Red (#67000d)
    if t < 0.5:
        s = t / 0.5
        r = int(8 + s * (255 - 8))
        g = int(48 + s * (255 - 48))
        b = int(107 + s * (255 - 107))
    else:
        s = (t - 0.5) / 0.5
        r = int(255 - s * (255 - 103))
        g = int(255 - s * 255)
        b = int(255 - s * (255 - 13))
    return f"#{r:02x}{g:02x}{b:02x}"


# Build series data with individual point colors
series_data = []
for i, (_year, anom) in enumerate(zip(years, anomalies, strict=True)):
    series_data.append({"x": i, "y": 1, "color": anomaly_to_color(anom)})

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 1600,
    "backgroundColor": "#ffffff",
    "margin": [0, 0, 50, 0],
    "spacing": [0, 0, 0, 0],
}

# Title - subtle, placed below the stripes
chart.options.title = {
    "text": "heatmap-stripes-climate \u00b7 highcharts \u00b7 pyplots.ai",
    "align": "center",
    "verticalAlign": "bottom",
    "y": -10,
    "style": {"fontSize": "24px", "color": "#999999", "fontWeight": "normal"},
}

# No axes visible
chart.options.x_axis = {"visible": False, "lineWidth": 0, "tickLength": 0, "min": -0.5, "max": n_years - 0.5}

chart.options.y_axis = {"visible": False, "lineWidth": 0, "gridLineWidth": 0, "min": 0, "max": 1}

# Remove legend
chart.options.legend = {"enabled": False}

# Remove credits
chart.options.credits = {"enabled": False}

# Plot options - no gaps between bars
chart.options.plot_options = {
    "column": {"pointPadding": 0, "groupPadding": 0, "borderWidth": 0, "animation": False},
    "series": {"enableMouseTracking": False},
}

# Tooltip disabled
chart.options.tooltip = {"enabled": False}

# Add series
series = ColumnSeries()
series.data = series_data
series.name = "Temperature Anomaly"
chart.add_series(series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width:4800px; height:1600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,1700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
