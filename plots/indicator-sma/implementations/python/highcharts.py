"""anyplot.ai
indicator-sma: Simple Moving Average (SMA) Indicator Chart
Library: highcharts unknown | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-19
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito colors (canonical order)
CLOSE_COLOR = "#009E73"  # position 1 — brand green — close price
SMA20_COLOR = "#D55E00"  # position 2 — vermillion — SMA 20
SMA50_COLOR = "#0072B2"  # position 3 — blue — SMA 50
SMA200_COLOR = "#CC79A7"  # position 4 — reddish purple — SMA 200

# Data: stock price with mean-reverting (Ornstein-Uhlenbeck) dynamics
np.random.seed(42)
n_days = 365
dates = pd.date_range(start="2024-01-02", periods=n_days, freq="B")

# Ornstein-Uhlenbeck mean-reverting process (differentiates from linear-trend peers)
theta = 0.008  # mean-reversion speed
mu = 175.0  # long-term mean
sigma = 0.015  # volatility
price = 150.0
prices = [price]
for _ in range(n_days - 1):
    drift = theta * (mu - prices[-1])
    noise = np.random.normal(0, sigma * prices[-1])
    prices.append(max(prices[-1] + drift + noise, 50.0))

close_prices = np.array(prices)

df = pd.DataFrame({"date": dates, "close": close_prices})
df["sma_20"] = df["close"].rolling(window=20).mean()
df["sma_50"] = df["close"].rolling(window=50).mean()
df["sma_200"] = df["close"].rolling(window=200).mean()

# Convert dates to milliseconds for Highcharts datetime axis
timestamps = [int(d.timestamp() * 1000) for d in df["date"]]

close_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["close"], strict=True)]
sma20_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["sma_20"], strict=True) if not np.isnan(v)]
sma50_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["sma_50"], strict=True) if not np.isnan(v)]
sma200_data = [[t, round(v, 2)] for t, v in zip(timestamps, df["sma_200"], strict=True) if not np.isnan(v)]

# Build chart via highcharts_core SDK
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "plotBorderWidth": 0,
    "marginBottom": 200,
    "marginLeft": 220,
    "marginRight": 100,
    "marginTop": 180,
    "style": {"fontFamily": "Arial, sans-serif"},
}

chart.options.title = {
    "text": "indicator-sma · python · highcharts · anyplot.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": INK},
    "y": 70,
}

chart.options.subtitle = {
    "text": "Stock Price with 20, 50, and 200-day Simple Moving Averages",
    "style": {"fontSize": "36px", "color": INK_SOFT},
    "y": 130,
}

# tickInterval = monthly; dateTimeLabelFormats eliminates year-boundary duplication
chart.options.x_axis = {
    "type": "datetime",
    "title": {"text": "Date", "style": {"fontSize": "40px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}, "y": 35},
    "tickInterval": 30 * 24 * 3600 * 1000,
    "dateTimeLabelFormats": {"month": "%b %Y", "year": "%Y"},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineWidth": 0,
    "tickWidth": 2,
    "tickColor": INK_SOFT,
    "tickLength": 12,
}

chart.options.y_axis = {
    "title": {"text": "Price (USD)", "style": {"fontSize": "40px", "color": INK}, "margin": 25},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}, "format": "${value:.0f}", "x": -15},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineWidth": 0,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -60,
    "y": 120,
    "itemStyle": {"fontSize": "28px", "color": INK_SOFT},
    "itemMarginBottom": 15,
    "symbolWidth": 40,
    "symbolHeight": 18,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.tooltip = {
    "shared": True,
    "valueDecimals": 2,
    "valuePrefix": "$",
    "headerFormat": '<span style="font-size: 22px">{point.key:%b %d, %Y}</span><br/>',
    "style": {"fontSize": "22px"},
}

chart.options.plot_options = {"line": {"lineWidth": 4, "marker": {"enabled": False}}, "series": {"animation": False}}

chart.options.credits = {"enabled": False}

# Build series using LineSeries SDK objects
series_specs = [
    ("Close Price", close_data, CLOSE_COLOR, 5, "Solid", 4),
    ("SMA 20", sma20_data, SMA20_COLOR, 3, "Solid", 3),
    ("SMA 50", sma50_data, SMA50_COLOR, 3, "ShortDash", 2),
    ("SMA 200", sma200_data, SMA200_COLOR, 3, "LongDash", 1),
]

series_list = []
for name, data, color, line_width, dash_style, z_index in series_specs:
    s = LineSeries()
    s.name = name
    s.data = data
    s.color = color
    s.line_width = line_width
    s.dash_style = dash_style
    s.z_index = z_index
    s.marker = {"enabled": False}
    series_list.append(s)

chart.options.series = series_list

# Download Highcharts JS from jsdelivr (inline embed required for headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@12/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=60) as response:
    highcharts_js = response.read().decode("utf-8")

chart_js = chart.to_js_literal()

# Inline HTML for headless screenshot
inline_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# CDN HTML for interactive artifact
cdn_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Save CDN HTML artifact for interactive viewing
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(cdn_html)

# Write temp inline HTML and screenshot for PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(inline_html)
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
