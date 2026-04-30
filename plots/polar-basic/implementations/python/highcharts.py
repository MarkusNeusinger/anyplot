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
from highcharts_core.options.series.area import AreaSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"

BRAND = "#009E73"  # Okabe-Ito position 1
PEAK_COLOR = "#D55E00"  # Okabe-Ito position 2 - peak highlight

# Data - 24-hour temperature cycle
np.random.seed(42)
hours = np.arange(0, 24)
base_temp = 15 + 10 * np.sin(np.radians(hours / 24 * 360 - 90))  # Peak around noon
temperatures = base_temp + np.random.randn(24) * 2

peak_idx = int(np.argmax(temperatures))

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Square canvas - optimal for circular polar chart
chart.options.chart = {
    "polar": True,
    "width": 3600,
    "height": 3600,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK},
    "marginTop": 240,
    "marginBottom": 220,
}

chart.options.title = {
    "text": "polar-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {"text": "24-Hour Temperature Pattern", "style": {"fontSize": "48px", "color": INK_SOFT}}

# Angular axis (hours)
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

# Radial axis (temperature)
chart.options.y_axis = {
    "min": 0,
    "max": 35,
    "tickInterval": 5,
    "labels": {"format": "{value}°C", "style": {"fontSize": "28px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
}

# Pane - generous in square canvas
chart.options.pane = {"size": "78%", "startAngle": 0, "endAngle": 360}

# Custom tooltip with formatted output (distinctive Highcharts feature)
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<span style='font-size:24px; font-weight:bold'>{series.name}</span><br/><b>{point.x}h</b>: {point.y:.1f}°C",
    "style": {"fontSize": "28px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 12,
}

chart.options.plot_options = {
    "area": {
        "connectEnds": True,
        "fillOpacity": 0.28,
        "lineWidth": 3,
        "marker": {"enabled": True, "radius": 12, "symbol": "circle", "lineWidth": 2, "lineColor": PAGE_BG},
    },
    "scatter": {"marker": {"radius": 22, "symbol": "circle"}},
    "series": {"animation": False},
}

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

chart.options.credits = {"enabled": False}

# Main temperature series - AreaSeries for filled polar trace
area_series = AreaSeries()
area_series.data = [[float(h), float(t)] for h, t in zip(hours, temperatures, strict=True)]
area_series.name = "Temperature"
area_series.color = BRAND
area_series.fill_opacity = 0.28
area_series.connect_ends = True

chart.add_series(area_series)

# Focal-point marker highlighting the daily maximum temperature
peak_series = ScatterSeries()
peak_series.data = [[float(hours[peak_idx]), float(temperatures[peak_idx])]]
peak_series.name = "Daily Peak"
peak_series.color = PEAK_COLOR
peak_series.marker = {"radius": 22, "symbol": "circle", "lineWidth": 3, "lineColor": INK}
peak_series.data_labels = {
    "enabled": True,
    "format": "{point.y:.1f}°C",
    "style": {"fontSize": "28px", "color": INK, "fontWeight": "bold", "textOutline": "none"},
    "y": -50,
}

chart.add_series(peak_series)

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
    <div id="container" style="width: 3600px; height: 3600px;"></div>
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
chrome_options.add_argument("--window-size=3800,3800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
