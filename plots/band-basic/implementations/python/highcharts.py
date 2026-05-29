"""anyplot.ai
band-basic: Basic Band Plot
Library: highcharts 1.10.3 | Python 3.14
Quality: 91/100 | Updated: 2026-05-29
"""

import os
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


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — first series always #009E73
BAND_COLOR = "#009E73"  # Imprint position 1
LINE_COLOR = "#BD8233"  # Imprint position 4 (ochre) — contrasts with green band

# Data — 30-day temperature forecast with 95% prediction interval
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

font_family = "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

# Title: "band-basic · python · highcharts · anyplot.ai" (46 chars < 67 — use default 66px)
title_text = "band-basic · python · highcharts · anyplot.ai"

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "marginBottom": 160,
    "marginLeft": 200,
    "marginRight": 100,
    "marginTop": 130,
    "style": {"fontFamily": font_family},
}

chart.options.title = {
    "text": title_text,
    "style": {"fontSize": "66px", "fontWeight": "bold", "color": INK, "fontFamily": font_family},
}

chart.options.subtitle = {
    "text": "30-day forecast with 95% prediction interval",
    "style": {"fontSize": "44px", "color": INK_SOFT, "fontFamily": font_family},
}

chart.options.x_axis = {
    "title": {
        "text": "Forecast Day",
        "style": {"fontSize": "56px", "color": INK, "fontFamily": font_family},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT, "fontFamily": font_family}},
    "gridLineWidth": 0,
    "tickInterval": 5,
    "lineColor": INK_SOFT,
    "lineWidth": 1,
    "tickColor": INK_SOFT,
    "tickLength": 8,
}

chart.options.y_axis = {
    "title": {
        "text": "Temperature (°C)",
        "style": {"fontSize": "56px", "color": INK, "fontFamily": font_family},
        "margin": 20,
    },
    "labels": {"format": "{value}°", "style": {"fontSize": "44px", "color": INK_SOFT, "fontFamily": font_family}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "lineWidth": 1,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 80,
    "floating": True,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "shadow": False,
    "itemStyle": {"fontSize": "44px", "fontWeight": "normal", "color": INK_SOFT, "fontFamily": font_family},
    "itemMarginBottom": 8,
    "symbolRadius": 4,
}

chart.options.plot_options = {
    "arearange": {"fillOpacity": 0.25, "lineWidth": 0, "marker": {"enabled": False}},
    "line": {"lineWidth": 4, "marker": {"enabled": False}},
}

chart.options.credits = {"enabled": False}

# Band series (AreaRange) — Imprint position 1
band = AreaRangeSeries()
band.data = band_data
band.name = "95% Prediction Interval"
band.color = BAND_COLOR
band.fill_opacity = 0.25
band.z_index = 0

# Forecast center line — Imprint position 4
forecast = LineSeries()
forecast.data = line_data
forecast.name = "Forecast"
forecast.color = LINE_COLOR
forecast.line_width = 4
forecast.z_index = 1

chart.add_series(band)
chart.add_series(forecast)

chart_js = chart.to_js_literal()

# Download Highcharts JS inline — headless Chrome cannot load CDN from file://
cdn_base = "https://cdn.jsdelivr.net/npm/highcharts@11.4"
js_urls = {"highcharts": f"{cdn_base}/highcharts.js", "highcharts_more": f"{cdn_base}/highcharts-more.js"}
js_modules = {}
for name, url in js_urls.items():
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        js_modules[name] = response.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_modules["highcharts"]}</script>
    <script>{js_modules["highcharts_more"]}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone is eaten by Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Normalize to exact 3200×1800 — guards against ±1-2 px rounding from headless Chrome
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")
