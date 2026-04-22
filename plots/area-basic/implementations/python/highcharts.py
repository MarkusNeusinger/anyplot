""" pyplots.ai
area-basic: Basic Area Chart
Library: highcharts 1.10.3 | Python 3.14.2
Quality: 93/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Daily website visitors over a month
np.random.seed(42)
days = np.arange(1, 31)
# Simulate website traffic with weekly pattern and growth trend
base_traffic = 2000 + days * 50  # Growth trend
weekly_pattern = 300 * np.sin(2 * np.pi * days / 7)  # Weekly cycle
noise = np.random.normal(0, 200, len(days))
visitors = base_traffic + weekly_pattern + noise
visitors = np.clip(visitors, 500, None).astype(int)

peak_day = int(days[np.argmax(visitors)])
peak_visitors = int(np.max(visitors))

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 300,
    "marginLeft": 220,
    "marginRight": 100,
    "spacingBottom": 40,
}

# Title
chart.options.title = {
    "text": "area-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# Subtitle for data context
chart.options.subtitle = {
    "text": "Daily Website Visitors Over One Month \u2014 Weekend Dips with Steady Growth",
    "style": {"fontSize": "42px", "color": "#666666"},
}

# X-axis with weekend plotBands (day 1 = Monday, so days 6-7, 13-14, 20-21, 27-28 are weekends)
weekend_bands = []
for d in range(1, 31):
    weekday = (d - 1) % 7  # 0=Mon, 5=Sat, 6=Sun
    if weekday in (5, 6):
        weekend_bands.append({"from": d - 0.5, "to": d + 0.5, "color": "rgba(48, 105, 152, 0.05)"})

chart.options.x_axis = {
    "title": {"text": "Day of Month", "style": {"fontSize": "48px"}, "margin": 30},
    "labels": {"style": {"fontSize": "36px"}, "y": 45},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.08)",
    "tickInterval": 1,
    "plotBands": weekend_bands,
    "crosshair": {"width": 2, "color": "rgba(48, 105, 152, 0.3)", "dashStyle": "Dash"},
}

# Y-axis with plotLine at peak
chart.options.y_axis = {
    "title": {"text": "Daily Visitors", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.08)",
    "min": 1500,
    "startOnTick": False,
    "plotLines": [
        {
            "value": peak_visitors,
            "color": "rgba(192, 57, 43, 0.5)",
            "width": 3,
            "dashStyle": "Dot",
            "label": {
                "text": f"\u25b2 Peak: {peak_visitors:,} visitors (Day {peak_day})",
                "align": "left",
                "x": 10,
                "y": -10,
                "style": {"fontSize": "32px", "color": "rgba(192, 57, 43, 0.8)", "fontWeight": "bold"},
            },
            "zIndex": 5,
        }
    ],
}

# Plot options with semi-transparent fill and gradient
chart.options.plot_options = {
    "area": {
        "fillColor": {
            "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
            "stops": [[0, "rgba(48, 105, 152, 0.5)"], [1, "rgba(48, 105, 152, 0.02)"]],
        },
        "lineWidth": 4,
        "marker": {"enabled": True, "radius": 6, "fillColor": "#306998", "lineWidth": 2, "lineColor": "#ffffff"},
        "color": "#306998",
        "tooltip": {"headerFormat": "<b>Day {point.x}</b><br/>", "pointFormat": "Visitors: {point.y:,.0f}"},
        "states": {"hover": {"lineWidthPlus": 2}},
    }
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "horizontal",
    "x": -40,
    "y": 60,
}

# Credits off
chart.options.credits = {"enabled": False}

# Tooltip styling
chart.options.tooltip = {
    "style": {"fontSize": "28px"},
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderColor": "#306998",
    "borderRadius": 8,
}

# Add series
series = AreaSeries()
series.data = [[int(d), int(v)] for d, v in zip(days, visitors, strict=True)]
series.name = "Website Visitors"
chart.add_series(series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

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
time.sleep(5)  # Wait for chart to render

driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
