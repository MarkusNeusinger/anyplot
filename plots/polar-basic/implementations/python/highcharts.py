""" anyplot.ai
polar-basic: Basic Polar Chart
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-04-30
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.20)" if THEME == "light" else "rgba(240,239,232,0.20)"

BRAND = "#009E73"  # Okabe-Ito position 1

# Data - 24-hour temperature cycle
np.random.seed(42)
hours = np.arange(0, 24)
base_temp = 15 + 10 * np.sin(np.radians(hours / 24 * 360 - 90))  # Peak around noon
temperatures = base_temp + np.random.randn(24) * 2

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "polar": True,
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
    "marginTop": 220,
}

# Title
chart.options.title = {
    "text": "polar-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold", "color": INK},
}

# Subtitle
chart.options.subtitle = {"text": "24-Hour Temperature Pattern", "style": {"fontSize": "48px", "color": INK_SOFT}}

# X-axis (angular - hours 0-24 map to 0-360°)
chart.options.x_axis = {
    "min": 0,
    "max": 24,
    "tickInterval": 3,
    "labels": {"format": "{value}h", "style": {"fontSize": "36px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

# Y-axis (radial - temperature), no rotated title to improve readability
chart.options.y_axis = {
    "min": 0,
    "max": 35,
    "tickInterval": 5,
    "labels": {"format": "{value}°C", "style": {"fontSize": "28px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
}

# Pane settings (startAngle 0 = top for time-based data)
chart.options.pane = {"size": "72%", "startAngle": 0, "endAngle": 360}

# Plot options
chart.options.plot_options = {
    "scatter": {"marker": {"enabled": True, "radius": 18, "symbol": "circle"}, "lineWidth": 3},
    "series": {"animation": False},
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "center",
    "verticalAlign": "bottom",
    "layout": "horizontal",
    "itemStyle": {"fontSize": "36px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

# Credits
chart.options.credits = {"enabled": False}

# Series
series = ScatterSeries()
series.data = [[float(h), float(t)] for h, t in zip(hours, temperatures, strict=True)]
series.name = "Temperature"
series.color = BRAND
series.marker = {"radius": 18, "symbol": "circle"}

chart.add_series(series)

# Download Highcharts JS (inline for headless Chrome, with /tmp cache)
cache_dir = Path("/tmp")
hc_urls = {
    "core": ("https://cdn.jsdelivr.net/npm/highcharts@11.4.8/highcharts.js", cache_dir / "highcharts.js"),
    "more": ("https://cdn.jsdelivr.net/npm/highcharts@11.4.8/highcharts-more.js", cache_dir / "highcharts-more.js"),
}
hc_js = {}
for key, (url, cache_path) in hc_urls.items():
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        hc_js[key] = cache_path.read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(url, timeout=30) as resp:
            content = resp.read().decode("utf-8")
        cache_path.write_text(content, encoding="utf-8")
        hc_js[key] = content
highcharts_js = hc_js["core"]
highcharts_more_js = hc_js["more"]

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

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
