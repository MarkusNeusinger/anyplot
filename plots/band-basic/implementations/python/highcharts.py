""" pyplots.ai
band-basic: Basic Band Plot
Library: highcharts 1.10.3 | Python 3.14
Quality: 91/100 | Updated: 2026-02-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Daily temperature forecast with 95% prediction interval
np.random.seed(42)
days = np.arange(1, 31)
temp_center = 12 + 0.3 * days + 4 * np.sin(days * 0.4)
uncertainty = 1.5 + 0.08 * days
temp_lower = temp_center - 1.96 * uncertainty
temp_upper = temp_center + 1.96 * uncertainty

band_data = [
    [int(d), round(float(lo), 1), round(float(hi), 1)] for d, lo, hi in zip(days, temp_lower, temp_upper, strict=True)
]
line_data = [[int(d), round(float(t), 1)] for d, t in zip(days, temp_center, strict=True)]

# Build chart using highcharts-core Python wrapper
font_family = "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 180,
    "marginLeft": 220,
    "marginRight": 100,
    "spacing": [40, 40, 40, 40],
    "style": {"fontFamily": font_family},
}

chart.options.title = {
    "text": "30-Day Temperature Forecast \u00b7 band-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "fontFamily": font_family},
}

chart.options.subtitle = {
    "text": "Daily forecast with 95% prediction interval",
    "style": {"fontSize": "30px", "color": "#666666", "fontFamily": font_family},
}

chart.options.x_axis = {
    "title": {
        "text": "Forecast Day",
        "style": {"fontSize": "36px", "color": "#444444", "fontFamily": font_family},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#555555", "fontFamily": font_family}},
    "gridLineWidth": 0,
    "tickInterval": 5,
    "lineColor": "rgba(0, 0, 0, 0.12)",
    "lineWidth": 1,
    "tickColor": "rgba(0, 0, 0, 0.12)",
    "tickLength": 8,
}

chart.options.y_axis = {
    "title": {
        "text": "Temperature (\u00b0C)",
        "style": {"fontSize": "36px", "color": "#444444", "fontFamily": font_family},
        "margin": 20,
    },
    "labels": {"format": "{value}\u00b0", "style": {"fontSize": "28px", "color": "#555555", "fontFamily": font_family}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "lineColor": "rgba(0, 0, 0, 0.12)",
    "lineWidth": 1,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 60,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.85)",
    "borderWidth": 0,
    "shadow": False,
    "itemStyle": {"fontSize": "28px", "fontWeight": "normal", "fontFamily": font_family},
    "itemMarginBottom": 8,
    "symbolRadius": 4,
}

chart.options.plot_options = {
    "arearange": {"fillOpacity": 0.25, "lineWidth": 0, "marker": {"enabled": False}},
    "line": {"lineWidth": 5, "marker": {"enabled": False}},
}

chart.options.credits = {"enabled": False}

# Band series using AreaRangeSeries
band = AreaRangeSeries()
band.data = band_data
band.name = "95% Prediction Interval"
band.color = "#306998"
band.fill_opacity = 0.25
band.z_index = 0

# Forecast line using LineSeries with refined deep amber color
forecast = LineSeries()
forecast.data = line_data
forecast.name = "Forecast"
forecast.color = "#C49000"
forecast.line_width = 5
forecast.z_index = 1

chart.add_series(band)
chart.add_series(forecast)

# Generate JS via highcharts-core wrapper
chart_js = chart.to_js_literal()

# Download Highcharts JS files for inline embedding (headless Chrome cannot load CDN)
cdn_base = "https://cdn.jsdelivr.net/npm/highcharts@11.4"
js_urls = {"highcharts": f"{cdn_base}/highcharts.js", "highcharts_more": f"{cdn_base}/highcharts-more.js"}
js_modules = {}
for name, url in js_urls.items():
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        js_modules[name] = response.read().decode("utf-8")

# Build HTML with inline Highcharts JS and chart literal from wrapper
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_modules["highcharts"]}</script>
    <script>{js_modules["highcharts_more"]}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
