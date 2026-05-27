""" anyplot.ai
bar-diverging: Diverging Bar Chart
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-08
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
POSITIVE = "#009E73"  # bluish green (brand, position 1)
NEGATIVE = "#AE3030"  # imprint red — negative

# Data - Customer satisfaction survey results by department
categories = [
    "Customer Service",
    "IT Support",
    "Sales",
    "Marketing",
    "Finance",
    "Operations",
    "HR",
    "R&D",
    "Legal",
    "Logistics",
]

# Net satisfaction scores: positive = more satisfied than dissatisfied
values = [45, 32, 28, 15, 8, -5, -12, -18, -25, -38]

# Separate positive and negative for different colors
positive_data = [{"y": v, "color": POSITIVE} if v >= 0 else {"y": v, "color": NEGATIVE} for v in values]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "bar",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginLeft": 280,
    "marginRight": 100,
}

# Title
chart.options.title = {"text": "bar-diverging · highcharts · anyplot.ai", "style": {"fontSize": "28px", "color": INK}}

# X-axis (categories)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
}

# Y-axis (values) - note: in horizontal bar, y_axis shows values
chart.options.y_axis = {
    "title": {"text": "Net Satisfaction Score", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
    "plotLines": [{"value": 0, "width": 2, "color": INK_SOFT, "zIndex": 5, "dashStyle": "Solid"}],
    "min": -50,
    "max": 60,
}

# Legend
chart.options.legend = {"enabled": False}

# Credits
chart.options.credits = {"enabled": False}

# Series
series = BarSeries()
series.name = "Net Satisfaction"
series.data = positive_data
series.data_labels = {"enabled": True, "style": {"fontSize": "18px", "color": INK}, "format": "{y}"}
series.border_width = 0
series.point_width = 80

chart.add_series(series)

# Plot options
chart.options.plot_options = {"bar": {"groupPadding": 0.1, "pointPadding": 0.05}}


# Download Highcharts JS (with fallback CDN)
def fetch_js(urls):
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except Exception:
            continue
    raise RuntimeError(f"Failed to download JS from: {urls}")


hc_urls = ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]
highcharts_js = fetch_js(hc_urls)

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")
chrome_options.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
