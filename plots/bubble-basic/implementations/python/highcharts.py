""" pyplots.ai
bubble-basic: Basic Bubble Chart
Library: highcharts 1.10.3 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-16
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bubble import BubbleSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Tech companies by sector
np.random.seed(42)

sectors = {
    "Cloud & SaaS": {
        "color": "rgba(48, 105, 152, 0.65)",
        "border": "#1e4f7a",
        "revenues": [12, 38, 68, 125, 200, 330, 500],
        "growth_base": [48, 35, 42, 28, 22, 15, 10],
    },
    "E-Commerce": {
        "color": "rgba(180, 90, 50, 0.65)",
        "border": "#8c3a1a",
        "revenues": [25, 75, 155, 270, 420, 600],
        "growth_base": [40, 30, 18, 14, 12, 6],
    },
    "Semiconductors": {
        "color": "rgba(60, 145, 80, 0.65)",
        "border": "#2a6e3a",
        "revenues": [5, 45, 95, 170, 300, 460],
        "growth_base": [52, 33, 25, 20, 16, 8],
    },
    "Social & Media": {
        "color": "rgba(140, 80, 160, 0.65)",
        "border": "#6b3480",
        "revenues": [8, 52, 110, 185, 245, 390, 550],
        "growth_base": [55, 38, 30, 22, 18, 12, 7],
    },
    "Fintech": {
        "color": "rgba(200, 160, 50, 0.65)",
        "border": "#9a7a1a",
        "revenues": [15, 82, 140, 220],
        "growth_base": [45, 28, 20, 15],
    },
}

# Build series data with realistic variation
all_series = []
for sector_name, sector in sectors.items():
    n = len(sector["revenues"])
    rev = np.array(sector["revenues"], dtype=float) + np.random.uniform(-3, 3, n)
    grw = np.array(sector["growth_base"], dtype=float) + np.random.uniform(-2, 2, n)
    cap = rev * (1 + grw / 100) * np.random.uniform(2.5, 7, n)

    data = [
        {"x": round(float(rev[i]), 1), "y": round(float(grw[i]), 1), "z": round(float(cap[i]), 1)} for i in range(n)
    ]

    s = BubbleSeries()
    s.name = sector_name
    s.data = data
    s.color = sector["color"]
    s.marker = {"lineWidth": 3, "lineColor": sector["border"]}
    all_series.append(s)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "bubble",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafafa",
    "spacing": [40, 60, 180, 60],
    "style": {"fontFamily": "'Segoe UI', Arial, sans-serif"},
}

chart.options.title = {
    "text": "bubble-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "60px", "fontWeight": "bold", "color": "#2a2a2a"},
}

chart.options.subtitle = {
    "text": "Bubble size represents Market Capitalization \u2014 Tech companies by sector",
    "style": {"fontSize": "38px", "color": "#666666"},
}

chart.options.x_axis = {
    "title": {"text": "Revenue (Billion USD)", "style": {"fontSize": "42px", "color": "#3a3a3a"}, "margin": 24},
    "labels": {"style": {"fontSize": "34px", "color": "#555555"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#cccccc",
    "lineWidth": 2,
    "tickColor": "#cccccc",
    "min": 0,
    "tickInterval": 100,
}

chart.options.y_axis = {
    "title": {"text": "Growth Rate (%)", "style": {"fontSize": "42px", "color": "#3a3a3a"}, "margin": 24},
    "labels": {"style": {"fontSize": "34px", "color": "#555555"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "lineColor": "#cccccc",
    "lineWidth": 2,
    "min": 0,
    "tickInterval": 10,
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -30,
    "y": 80,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.85)",
    "borderColor": "#dddddd",
    "borderWidth": 1,
    "borderRadius": 8,
    "padding": 20,
    "itemStyle": {"fontSize": "32px", "fontWeight": "normal", "color": "#333333"},
    "itemMarginBottom": 10,
    "symbolRadius": 6,
    "bubbleLegend": {
        "enabled": True,
        "borderColor": "#888888",
        "borderWidth": 2,
        "color": "rgba(200, 200, 200, 0.3)",
        "connectorColor": "#999999",
        "connectorWidth": 2,
        "labels": {"style": {"fontSize": "26px", "color": "#555555"}, "format": "{value:.0f}B"},
        "minSize": 16,
        "maxSize": 55,
    },
}

chart.options.tooltip = {
    "useHTML": True,
    "headerFormat": '<span style="font-size: 28px; font-weight: bold; color: {series.color}">{series.name}</span><br/>',
    "pointFormat": '<span style="font-size: 24px">Revenue: <b>${point.x:.1f}B</b><br/>'
    "Growth: <b>{point.y:.1f}%</b><br/>"
    "Market Cap: <b>${point.z:.0f}B</b></span>",
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#cccccc",
    "borderRadius": 8,
    "shadow": {"color": "rgba(0, 0, 0, 0.15)", "offsetX": 2, "offsetY": 2, "width": 4},
}

chart.options.plot_options = {
    "bubble": {"minSize": 30, "maxSize": 200, "sizeBy": "area", "dataLabels": {"enabled": False}, "zMin": 0}
}

for s in all_series:
    chart.add_series(s)

# Download Highcharts JS and highcharts-more.js for bubble support
highcharts_url = "https://code.highcharts.com/highcharts.js"
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
