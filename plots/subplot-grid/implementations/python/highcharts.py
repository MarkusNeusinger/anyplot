""" pyplots.ai
subplot-grid: Subplot Grid Layout
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

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


# Create 4 separate charts for the grid
# Chart 1: Price Line Chart (top-left)
chart1 = Chart(container="container1")
chart1.options = HighchartsOptions()
chart1.options.chart = {
    "type": "line",
    "width": 2300,
    "height": 1250,
    "backgroundColor": "#ffffff",
    "marginBottom": 100,
}
chart1.options.title = {"text": "Stock Price Trend", "style": {"fontSize": "32px", "fontWeight": "bold"}}
chart1.options.x_axis = {
    "title": {"text": "Trading Day", "style": {"fontSize": "24px"}},
    "labels": {"style": {"fontSize": "20px"}, "format": "Day {value}"},
    "tickInterval": 10,
    "min": 0,
    "max": days - 1,
}
chart1.options.y_axis = {
    "title": {"text": "Price ($)", "style": {"fontSize": "24px"}},
    "labels": {"style": {"fontSize": "18px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}
chart1.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "20px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -20,
    "y": 60,
    "floating": True,
    "backgroundColor": "rgba(255,255,255,0.9)",
    "borderWidth": 1,
    "borderColor": "#e0e0e0",
}
chart1.options.plot_options = {"line": {"lineWidth": 4, "marker": {"radius": 0}}}

price_series = LineSeries()
price_series.data = [{"x": i, "y": float(p)} for i, p in enumerate(prices)]
price_series.name = "Price"
price_series.color = "#306998"
chart1.add_series(price_series)

ma_series = LineSeries()
ma_series.data = [{"x": i + ma_window - 1, "y": float(m)} for i, m in enumerate(ma)]
ma_series.name = f"{ma_window}-Day MA"
ma_series.color = "#FFD43B"
ma_series.dash_style = "Dash"
chart1.add_series(ma_series)


# Chart 2: Volume Bar Chart (top-right)
chart2 = Chart(container="container2")
chart2.options = HighchartsOptions()
chart2.options.chart = {
    "type": "column",
    "width": 2300,
    "height": 1250,
    "backgroundColor": "#ffffff",
    "marginBottom": 100,
}
chart2.options.title = {"text": "Trading Volume", "style": {"fontSize": "32px", "fontWeight": "bold"}}
chart2.options.x_axis = {
    "title": {"text": "Trading Day", "style": {"fontSize": "24px"}},
    "labels": {"style": {"fontSize": "20px"}, "format": "Day {value}"},
    "tickInterval": 10,
    "min": 0,
    "max": days - 1,
}
chart2.options.y_axis = {
    "title": {"text": "Volume (shares)", "style": {"fontSize": "24px"}},
    "labels": {"style": {"fontSize": "18px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}
chart2.options.legend = {"enabled": False}
chart2.options.plot_options = {"column": {"borderWidth": 0, "pointPadding": 0.1}}

volume_series = ColumnSeries()
volume_series.data = [{"x": i, "y": float(v)} for i, v in enumerate(volumes)]
volume_series.name = "Volume"
volume_series.color = "#306998"
chart2.add_series(volume_series)


# Chart 3: Returns Histogram (bottom-left)
# Create histogram bins manually
hist_counts, bin_edges = np.histogram(returns, bins=15)
bin_centers = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(len(bin_edges) - 1)]
bin_labels = [f"{b:.1f}%" for b in bin_centers]

chart3 = Chart(container="container3")
chart3.options = HighchartsOptions()
chart3.options.chart = {
    "type": "column",
    "width": 2300,
    "height": 1250,
    "backgroundColor": "#ffffff",
    "marginBottom": 120,
}
chart3.options.title = {"text": "Daily Returns Distribution", "style": {"fontSize": "32px", "fontWeight": "bold"}}
chart3.options.x_axis = {
    "categories": bin_labels,
    "title": {"text": "Return (%)", "style": {"fontSize": "24px"}},
    "labels": {"style": {"fontSize": "18px"}, "rotation": 0},
}
chart3.options.y_axis = {
    "title": {"text": "Frequency", "style": {"fontSize": "24px"}},
    "labels": {"style": {"fontSize": "18px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}
chart3.options.legend = {"enabled": False}
chart3.options.plot_options = {"column": {"borderWidth": 0, "pointPadding": 0}}

hist_series = ColumnSeries()
hist_series.data = [int(c) for c in hist_counts]
hist_series.name = "Frequency"
hist_series.color = "#FFD43B"
chart3.add_series(hist_series)


# Chart 4: Price vs Volume Scatter (bottom-right)
chart4 = Chart(container="container4")
chart4.options = HighchartsOptions()
chart4.options.chart = {
    "type": "scatter",
    "width": 2300,
    "height": 1250,
    "backgroundColor": "#ffffff",
    "marginBottom": 100,
}
chart4.options.title = {"text": "Price vs Volume Relationship", "style": {"fontSize": "32px", "fontWeight": "bold"}}
chart4.options.x_axis = {
    "title": {"text": "Stock Price ($)", "style": {"fontSize": "24px"}},
    "labels": {"style": {"fontSize": "18px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}
chart4.options.y_axis = {
    "title": {"text": "Volume (shares)", "style": {"fontSize": "24px"}},
    "labels": {"style": {"fontSize": "18px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}
chart4.options.legend = {"enabled": False}
chart4.options.plot_options = {"scatter": {"marker": {"radius": 10, "symbol": "circle"}}}

scatter_series = ScatterSeries()
scatter_series.data = [[float(p), float(v)] for p, v in zip(prices, volumes, strict=True)]
scatter_series.name = "Price vs Volume"
scatter_series.color = "#9467BD"
chart4.add_series(scatter_series)


# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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
            background: #ffffff;
            font-family: Arial, sans-serif;
        }}
        .main-title {{
            text-align: center;
            font-size: 48px;
            font-weight: bold;
            color: #333;
            margin-bottom: 30px;
        }}
        .grid-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 50px;
            width: 4700px;
            height: 2550px;
        }}
        .chart-cell {{
            background: #ffffff;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
        }}
    </style>
</head>
<body>
    <div class="main-title">subplot-grid · highcharts · pyplots.ai</div>
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
with open("plot.html", "w", encoding="utf-8") as f:
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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
