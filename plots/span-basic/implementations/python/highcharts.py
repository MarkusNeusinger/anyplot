"""anyplot.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: highcharts | Python 3.13
Quality: 93/100 | Created: 2025-12-23
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

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
BRAND = "#009E73"  # Okabe-Ito position 1 — always first series

# Data - S&P 500 approximate quarterly closing values during the 2007-2010 financial crisis
quarters = [
    "Q1 2007",
    "Q2 2007",
    "Q3 2007",
    "Q4 2007",
    "Q1 2008",
    "Q2 2008",
    "Q3 2008",
    "Q4 2008",
    "Q1 2009",
    "Q2 2009",
    "Q3 2009",
    "Q4 2009",
    "Q1 2010",
    "Q2 2010",
    "Q3 2010",
    "Q4 2010",
]
sp500_values = [1421, 1503, 1527, 1468, 1323, 1280, 1166, 903, 798, 919, 1057, 1115, 1169, 1031, 1141, 1258]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "line",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 220,
    "spacingTop": 40,
}

chart.options.title = {
    "text": "span-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {
    "text": "S&P 500 Index with Financial Crisis Period Highlighted",
    "style": {"fontSize": "48px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "categories": quarters,
    "title": {"text": "Quarter", "style": {"fontSize": "44px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "32px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    # Vertical span — highlight financial crisis (Q4 2007 through Q1 2009, indices 3–8)
    "plotBands": [
        {
            "from": 3.5,
            "to": 8.5,
            "color": "rgba(213,94,0,0.18)",
            "label": {
                "text": "Financial Crisis",
                "style": {"fontSize": "40px", "color": "#D55E00", "fontWeight": "bold"},
                "verticalAlign": "top",
                "y": 80,
            },
        }
    ],
}

chart.options.y_axis = {
    "title": {"text": "Index Value (Points)", "style": {"fontSize": "44px", "color": INK}},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "min": 600,
    "max": 1700,
    # Horizontal span — highlight bear market zone (below 1000 points)
    "plotBands": [
        {
            "from": 600,
            "to": 1000,
            "color": "rgba(230,159,0,0.18)",
            "label": {
                "text": "Bear Market Zone",
                "style": {"fontSize": "36px", "color": "#E69F00", "fontWeight": "500"},
                "align": "left",
                "x": 40,
                "y": -15,
            },
        }
    ],
}

chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px", "color": INK_SOFT, "fontWeight": "normal"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
}

chart.options.plot_options = {"line": {"lineWidth": 6, "marker": {"radius": 12, "enabled": True}}}

series = LineSeries()
series.name = "S&P 500"
series.data = sp500_values
series.color = BRAND
series.marker = {"fillColor": BRAND, "lineColor": PAGE_BG, "lineWidth": 2}
chart.add_series(series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
