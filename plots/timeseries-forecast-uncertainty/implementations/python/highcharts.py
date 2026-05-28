""" anyplot.ai
timeseries-forecast-uncertainty: Time Series Forecast with Uncertainty Band
Library: highcharts unknown | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-19
"""

import os
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
FORECAST_BG = "rgba(196, 117, 253, 0.06)" if THEME == "light" else "rgba(196, 117, 253, 0.10)"

# Okabe-Ito palette (sequential positions)
BRAND = "#009E73"  # position 1 — historical data
FORECAST_COLOR = "#C475FD"  # position 2 — forecast line
CI_COLOR = "#4467A3"  # position 3 — both CI bands (opacity differentiates)

# Theme-adaptive CI fill opacity for dark-mode distinction
FILL_OP_80 = 0.30 if THEME == "light" else 0.40
FILL_OP_95 = 0.15 if THEME == "light" else 0.32

# Data — monthly product demand with 3-year history and 12-month ARIMA-style forecast
np.random.seed(42)

n_historical = 36
n_forecast = 12

start_date = datetime(2022, 1, 1)
historical_dates = [start_date + timedelta(days=30 * i) for i in range(n_historical)]
forecast_dates = [historical_dates[-1] + timedelta(days=30 * (i + 1)) for i in range(n_forecast)]

trend = np.linspace(100, 150, n_historical)
seasonality = 20 * np.sin(np.linspace(0, 6 * np.pi, n_historical))
noise = np.random.normal(0, 8, n_historical)
historical_values = trend + seasonality + noise

last_value = historical_values[-1]
forecast_trend = np.linspace(last_value, last_value + 20, n_forecast)
forecast_seasonality = 20 * np.sin(np.linspace(6 * np.pi, 8 * np.pi, n_forecast))
forecast_values = forecast_trend + forecast_seasonality

time_factor = np.linspace(1, 3, n_forecast)
ci_80 = 10 * time_factor
ci_95 = 18 * time_factor

lower_80 = forecast_values - ci_80
upper_80 = forecast_values + ci_80
lower_95 = forecast_values - ci_95
upper_95 = forecast_values + ci_95

historical_timestamps = [int(d.timestamp() * 1000) for d in historical_dates]
forecast_timestamps = [int(d.timestamp() * 1000) for d in forecast_dates]
forecast_start_ts = forecast_timestamps[0]
forecast_end_ts = forecast_timestamps[-1] + 30 * 24 * 3600 * 1000

# Download Highcharts JS with fallback URLs and per-URL retry
hc_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.min.js",
    "https://unpkg.com/highcharts@11/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
]
highcharts_js = None
for url in hc_urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
            break
        except (urllib.error.URLError, urllib.error.HTTPError):
            if attempt == 0:
                time.sleep(1)
    if highcharts_js:
        break
if not highcharts_js:
    raise RuntimeError("Could not download Highcharts from any CDN")

hc_more_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.min.js",
    "https://unpkg.com/highcharts@11/highcharts-more.js",
    "https://code.highcharts.com/highcharts-more.js",
]
highcharts_more_js = None
for url in hc_more_urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_more_js = response.read().decode("utf-8")
            break
        except (urllib.error.URLError, urllib.error.HTTPError):
            if attempt == 0:
                time.sleep(1)
    if highcharts_more_js:
        break
if not highcharts_more_js:
    raise RuntimeError("Could not download Highcharts More from any CDN")

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "borderWidth": 0,
    "plotBorderWidth": 0,
    "spacingTop": 40,
    "spacingBottom": 180,
    "spacingLeft": 60,
    "spacingRight": 80,
}

chart.options.title = {
    "text": "timeseries-forecast-uncertainty · python · highcharts · anyplot.ai",
    "style": {"fontSize": "66px", "fontWeight": "medium", "color": INK},
    "margin": 30,
}

chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "56px", "color": INK}, "margin": 15},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "dateTimeLabelFormats": {"month": "%b %Y"},
    "crosshair": {"color": GRID, "width": 2, "snap": True},
    "gridLineWidth": 0,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "plotLines": [
        {
            "value": forecast_start_ts,
            "color": INK_SOFT,
            "width": 2,
            "dashStyle": "Dash",
            "label": {
                "text": "Forecast Start",
                "style": {"fontSize": "38px", "color": INK_SOFT, "fontWeight": "normal"},
                "rotation": 0,
                "y": -10,
            },
            "zIndex": 5,
        }
    ],
    "plotBands": [{"from": forecast_start_ts, "to": forecast_end_ts, "color": FORECAST_BG}],
}

chart.options.y_axis = {
    "title": {"text": "Product Demand (Units)", "style": {"fontSize": "56px", "color": INK}, "margin": 15},
    "labels": {"style": {"fontSize": "44px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "itemStyle": {"fontSize": "44px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "symbolWidth": 28,
    "symbolHeight": 16,
    "symbolRadius": 3,
    "margin": 20,
    "padding": 16,
}

chart.options.tooltip = {
    "shared": True,
    "style": {"fontSize": "36px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "xDateFormat": "%B %Y",
    "valueDecimals": 1,
}

chart.options.plot_options = {"line": {"lineWidth": 4, "marker": {"radius": 6}}, "arearange": {"lineWidth": 0}}

# 95% CI outer band — lighter opacity creates visual nesting
ci_95_series = AreaRangeSeries()
ci_95_series.name = "95% Confidence Interval"
ci_95_series.data = [
    {"x": forecast_timestamps[i], "low": float(lower_95[i]), "high": float(upper_95[i])} for i in range(n_forecast)
]
ci_95_series.color = CI_COLOR
ci_95_series.fill_opacity = FILL_OP_95
ci_95_series.line_width = 0
ci_95_series.marker = {"enabled": False}
ci_95_series.z_index = 0

# 80% CI inner band — higher opacity stands out in front
ci_80_series = AreaRangeSeries()
ci_80_series.name = "80% Confidence Interval"
ci_80_series.data = [
    {"x": forecast_timestamps[i], "low": float(lower_80[i]), "high": float(upper_80[i])} for i in range(n_forecast)
]
ci_80_series.color = CI_COLOR
ci_80_series.fill_opacity = FILL_OP_80
ci_80_series.line_width = 0
ci_80_series.marker = {"enabled": False}
ci_80_series.z_index = 1

# Historical series — Okabe-Ito position 1 (brand green)
historical_series = LineSeries()
historical_series.name = "Historical (Actual)"
historical_series.data = [
    {"x": historical_timestamps[i], "y": float(historical_values[i])} for i in range(n_historical)
]
historical_series.color = BRAND
historical_series.line_width = 4
historical_series.marker = {"enabled": True, "radius": 5, "symbol": "circle"}
historical_series.z_index = 3

# Forecast series — Okabe-Ito position 2 (vermillion)
forecast_series = LineSeries()
forecast_series.name = "Forecast"
forecast_series.data = [{"x": forecast_timestamps[i], "y": float(forecast_values[i])} for i in range(n_forecast)]
forecast_series.color = FORECAST_COLOR
forecast_series.line_width = 4
forecast_series.dash_style = "Dash"
forecast_series.marker = {"enabled": True, "radius": 5, "symbol": "diamond"}
forecast_series.z_index = 4

chart.add_series(ci_95_series)
chart.add_series(ci_80_series)
chart.add_series(historical_series)
chart.add_series(forecast_series)

chart.options.credits = {"enabled": False}

# Generate HTML with inline scripts (CDN cannot be loaded from file:// in headless Chrome)
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
