""" anyplot.ai
subplot-grid: Subplot Grid Layout
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-13
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
from highcharts_core.options.series.bar import ColumnSeries
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

# Okabe-Ito palette
BRAND = "#009E73"  # First series - ALWAYS
COLOR2 = "#C475FD"
COLOR3 = "#4467A3"
COLOR4 = "#BD8233"

# Data - Financial dashboard with price, volume, returns
np.random.seed(42)
days = 60
dates = [f"Day {i + 1}" for i in range(days)]

# Stock price (random walk)
price_changes = np.random.randn(days) * 2
prices = 100 + np.cumsum(price_changes)

# Volume (random with some correlation to price change magnitude)
volumes = 50000 + np.abs(price_changes) * 15000 + np.random.randn(days) * 10000
volumes = np.maximum(volumes, 10000)

# Daily returns (percentage)
returns = (price_changes / prices) * 100

# Moving average for price
ma_window = 10
ma = np.convolve(prices, np.ones(ma_window) / ma_window, mode="valid")

# Chart 1: Price Line Chart (top-left)
chart1 = Chart(container="container1")
chart1.options = HighchartsOptions()
chart1.options.chart = {"type": "line", "width": 2300, "height": 1250, "backgroundColor": PAGE_BG, "marginBottom": 120}
chart1.options.title = {"text": "Stock Price Trend", "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK}}
chart1.options.x_axis = {
    "title": {"text": "Trading Day", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "Day {value}"},
    "tickInterval": 10,
    "min": 0,
    "max": days - 1,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}
chart1.options.y_axis = {
    "title": {"text": "Price ($)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}
chart1.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "16px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
}
chart1.options.plot_options = {"line": {"lineWidth": 3, "marker": {"radius": 0}}}

price_series = LineSeries()
price_series.data = [{"x": i, "y": float(p)} for i, p in enumerate(prices)]
price_series.name = "Price"
price_series.color = BRAND
chart1.add_series(price_series)

ma_series = LineSeries()
ma_series.data = [{"x": i + ma_window - 1, "y": float(m)} for i, m in enumerate(ma)]
ma_series.name = f"{ma_window}-Day MA"
ma_series.color = COLOR2
ma_series.dash_style = "Dash"
chart1.add_series(ma_series)

# Chart 2: Volume Bar Chart (top-right)
chart2 = Chart(container="container2")
chart2.options = HighchartsOptions()
chart2.options.chart = {
    "type": "column",
    "width": 2300,
    "height": 1250,
    "backgroundColor": PAGE_BG,
    "marginBottom": 120,
}
chart2.options.title = {"text": "Trading Volume", "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK}}
chart2.options.x_axis = {
    "title": {"text": "Trading Day", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}, "format": "Day {value}"},
    "tickInterval": 10,
    "min": 0,
    "max": days - 1,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}
chart2.options.y_axis = {
    "title": {"text": "Volume (shares)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}
chart2.options.legend = {"enabled": False}
chart2.options.plot_options = {"column": {"borderWidth": 0, "pointPadding": 0.1}}

volume_series = ColumnSeries()
volume_series.data = [{"x": i, "y": float(v)} for i, v in enumerate(volumes)]
volume_series.name = "Volume"
volume_series.color = BRAND
chart2.add_series(volume_series)

# Chart 3: Returns Histogram (bottom-left)
hist_counts, bin_edges = np.histogram(returns, bins=15)
bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(len(bin_edges) - 1)]
bin_labels = [f"{b:.1f}%" for b in bin_centers]

chart3 = Chart(container="container3")
chart3.options = HighchartsOptions()
chart3.options.chart = {
    "type": "column",
    "width": 2300,
    "height": 1250,
    "backgroundColor": PAGE_BG,
    "marginBottom": 160,
}
chart3.options.title = {
    "text": "Daily Returns Distribution",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}
chart3.options.x_axis = {
    "categories": bin_labels,
    "title": {"text": "Return (%)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "16px", "color": INK_SOFT}, "rotation": 45},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}
chart3.options.y_axis = {
    "title": {"text": "Frequency", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}
chart3.options.legend = {"enabled": False}
chart3.options.plot_options = {"column": {"borderWidth": 0, "pointPadding": 0}}

hist_series = ColumnSeries()
hist_series.data = [int(c) for c in hist_counts]
hist_series.name = "Frequency"
hist_series.color = BRAND
chart3.add_series(hist_series)

# Chart 4: Price vs Volume Scatter (bottom-right)
chart4 = Chart(container="container4")
chart4.options = HighchartsOptions()
chart4.options.chart = {
    "type": "scatter",
    "width": 2300,
    "height": 1250,
    "backgroundColor": PAGE_BG,
    "marginBottom": 120,
}
chart4.options.title = {"text": "Price vs Volume", "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK}}
chart4.options.x_axis = {
    "title": {"text": "Stock Price ($)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}
chart4.options.y_axis = {
    "title": {"text": "Volume (shares)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}
chart4.options.legend = {"enabled": False}
chart4.options.plot_options = {"scatter": {"marker": {"radius": 8}}}

scatter_series = ScatterSeries()
scatter_series.data = [[float(p), float(v)] for p, v in zip(prices, volumes, strict=True)]
scatter_series.name = "Price vs Volume"
scatter_series.color = BRAND
chart4.add_series(scatter_series)


# Download Highcharts JS with fallback CDNs
def download_js(urls, timeout=30, max_retries=2):
    if not isinstance(urls, list):
        urls = [urls]
    for url in urls:
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    return response.read().decode("utf-8")
            except Exception:
                if attempt == max_retries - 1:
                    continue
                time.sleep(1)
    raise RuntimeError("Failed to download Highcharts from all sources")


highcharts_urls = [
    "https://cdn.jsdelivr.net/npm/highcharts@11.4.3/highcharts.js",
    "https://code.highcharts.com/highcharts.js",
]
highcharts_js = download_js(highcharts_urls)

# Generate JS for all charts
js1 = chart1.to_js_literal()
js2 = chart2.to_js_literal()
js3 = chart3.to_js_literal()
js4 = chart4.to_js_literal()

# Create HTML with 2x2 grid layout
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        body {{
            margin: 0;
            padding: 50px;
            background: {PAGE_BG};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .main-title {{
            text-align: center;
            font-size: 32px;
            font-weight: 600;
            color: {INK};
            margin-bottom: 40px;
            letter-spacing: -0.5px;
        }}
        .grid-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 40px;
            width: 4700px;
            height: 2550px;
        }}
        .chart-cell {{
            background: {PAGE_BG};
            border: 1px solid {INK_SOFT};
            border-radius: 8px;
            overflow: hidden;
        }}
    </style>
</head>
<body>
    <div class="main-title">subplot-grid · highcharts · anyplot.ai</div>
    <div class="grid-container">
        <div class="chart-cell" id="container1"></div>
        <div class="chart-cell" id="container2"></div>
        <div class="chart-cell" id="container3"></div>
        <div class="chart-cell" id="container4"></div>
    </div>
    <script>
        {js1}
        {js2}
        {js3}
        {js4}
    </script>
</body>
</html>"""

# Save HTML file
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with Selenium
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
