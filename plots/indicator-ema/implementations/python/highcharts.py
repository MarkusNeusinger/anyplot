""" anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-19
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data
np.random.seed(42)
n_days = 120
base_price = 150.0
daily_returns = np.random.normal(0.001, 0.02, n_days)

prices = [base_price]
for ret in daily_returns[1:]:
    prices.append(prices[-1] * (1 + ret))

dates = pd.date_range(start="2024-06-01", periods=n_days, freq="B")
df = pd.DataFrame({"close": prices}, index=dates)
df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()

# Find crossover points
df["above"] = df["ema_12"] > df["ema_26"]
df["crossover"] = df["above"].astype(int).diff().fillna(0).abs() > 0
crossover_df = df[df["crossover"]]

timestamps = [int(d.timestamp() * 1000) for d in df.index]
crossover_timestamps = [int(d.timestamp() * 1000) for d in crossover_df.index]

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "spacingTop": 60,
    "spacingBottom": 100,
    "spacingLeft": 80,
    "spacingRight": 80,
}

chart.options.title = {
    "text": "Stock Price EMAs · indicator-ema · python · highcharts · anyplot.ai",
    "style": {"fontSize": "40px", "fontWeight": "bold", "color": INK},
    "margin": 40,
}

chart.options.subtitle = {
    "text": "Close Price with 12-day and 26-day Exponential Moving Averages",
    "style": {"fontSize": "30px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "36px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "tickInterval": 30 * 24 * 3600 * 1000,
    "dateTimeLabelFormats": {"month": "%b %Y"},
}

chart.options.y_axis = {
    "title": {"text": "Price (USD)", "style": {"fontSize": "36px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}, "format": "${value:.0f}"},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "margin": 30,
}

chart.options.tooltip = {
    "shared": True,
    "crosshairs": True,
    "style": {"fontSize": "24px"},
    "valueDecimals": 2,
    "valuePrefix": "$",
    "xDateFormat": "%b %d, %Y",
    "backgroundColor": ELEVATED_BG,
}

chart.options.plot_options = {
    "line": {"lineWidth": 5, "marker": {"enabled": False}, "states": {"hover": {"lineWidth": 6}}}
}

# Price series — Okabe-Ito position 1 (first categorical series)
price_series = LineSeries()
price_series.name = "Close Price"
price_series.data = [[t, round(p, 2)] for t, p in zip(timestamps, df["close"], strict=True)]
price_series.color = OKABE_ITO[0]
price_series.line_width = 5
price_series.z_index = 3
chart.add_series(price_series)

# EMA 12 series — Okabe-Ito position 2
ema12_series = LineSeries()
ema12_series.name = "EMA 12"
ema12_series.data = [[t, round(e, 2)] for t, e in zip(timestamps, df["ema_12"], strict=True)]
ema12_series.color = OKABE_ITO[1]
ema12_series.line_width = 3
ema12_series.z_index = 2
chart.add_series(ema12_series)

# EMA 26 series — Okabe-Ito position 3
ema26_series = LineSeries()
ema26_series.name = "EMA 26"
ema26_series.data = [[t, round(e, 2)] for t, e in zip(timestamps, df["ema_26"], strict=True)]
ema26_series.color = OKABE_ITO[2]
ema26_series.line_width = 3
ema26_series.dash_style = "ShortDash"
ema26_series.z_index = 1
chart.add_series(ema26_series)

# Crossover scatter points — Okabe-Ito position 4
crossover_series = ScatterSeries()
crossover_series.name = "Crossover"
crossover_series.data = [[t, round(e, 2)] for t, e in zip(crossover_timestamps, crossover_df["ema_12"], strict=True)]
crossover_series.color = OKABE_ITO[3]
crossover_series.marker = {"symbol": "diamond", "radius": 14}
crossover_series.z_index = 4
chart.add_series(crossover_series)

# Download Highcharts JS for inline embedding (try multiple CDNs)
cdn_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.min.js",
    "https://unpkg.com/highcharts@11/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
]

highcharts_js = None
for url in cdn_urls:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                highcharts_js = response.read().decode("utf-8")
                break
        except (urllib.error.URLError, urllib.error.HTTPError):
            if attempt < 1:
                time.sleep(1)
    if highcharts_js:
        break

if not highcharts_js:
    raise RuntimeError("Could not download Highcharts from any CDN")

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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
