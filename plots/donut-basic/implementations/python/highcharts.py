"""anyplot.ai
donut-basic: Basic Donut Chart
Library: highcharts | Python 3.14
Quality: pending | Updated: 2026-04-24
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.pie import PieSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first segment is always brand green)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data - Annual budget allocation by department (USD thousands)
categories = ["Engineering", "Operations", "Marketing", "Sales", "Support"]
values = [480, 210, 155, 125, 55]
total = sum(values)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "pie",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK, "fontFamily": "Helvetica, Arial, sans-serif"},
}

chart.options.title = {
    "text": "Budget by Department · donut-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "56px", "fontWeight": "500", "color": INK},
    "margin": 40,
}

# Center metric (two-line subtitle)
chart.options.subtitle = {
    "text": f'<div style="text-align:center;line-height:1.2;">'
    f'<div style="font-size:44px;color:{INK_SOFT};">Total budget</div>'
    f'<div style="font-size:112px;font-weight:700;color:{INK};">${total:,}K</div>'
    f"</div>",
    "useHTML": True,
    "align": "center",
    "verticalAlign": "middle",
    "y": 0,
}

chart.options.colors = OKABE_ITO

chart.options.plot_options = {
    "pie": {
        "innerSize": "58%",
        "size": "80%",
        "borderColor": PAGE_BG,
        "borderWidth": 8,
        "dataLabels": {
            "enabled": True,
            "format": "<b>{point.name}</b><br>{point.percentage:.1f}%",
            "distance": 80,
            "style": {"fontSize": "44px", "fontWeight": "normal", "color": INK, "textOutline": "none"},
            "connectorColor": INK_SOFT,
            "connectorWidth": 3,
        },
        "showInLegend": False,
        "states": {"hover": {"brightness": 0.05}},
    }
}

chart.options.legend = {"enabled": False}

chart.options.credits = {"enabled": False}

series = PieSeries()
series.name = "Budget"
series.data = [{"name": cat, "y": val} for cat, val in zip(categories, values, strict=True)]
chart.add_series(series)

# Download Highcharts JS for inline embedding (headless Chrome cannot load CDN from file://)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
req = urllib.request.Request(highcharts_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as response:
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

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Render PNG via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=4800,2820")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
