""" anyplot.ai
rug-basic: Basic Rug Plot
Library: highcharts unknown | Python 3.13.13
Quality: 83/100 | Updated: 2026-04-30
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
TICK_COLOR = "rgba(0, 158, 115, 0.7)"  # #009E73 (Okabe-Ito pos 1) with alpha

# Data
np.random.seed(42)
values = np.concatenate(
    [
        np.random.normal(50, 8, 40),  # Fast responses cluster
        np.random.normal(120, 15, 35),  # Medium responses cluster
        np.random.normal(250, 20, 15),  # Slow responses cluster
        np.array([380, 420, 510]),  # Outliers
    ]
)
values = np.clip(values, 10, 600)

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 200,
    "marginTop": 250,
    "marginLeft": 150,
    "marginRight": 150,
}

chart.options.title = {
    "text": "rug-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold", "color": INK},
}

chart.options.subtitle = {"text": "API Response Times (ms)", "style": {"fontSize": "48px", "color": INK_SOFT}}

chart.options.x_axis = {
    "title": {"text": "Response Time (ms)", "style": {"fontSize": "48px", "color": INK}},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "gridLineWidth": 0,
    "min": 0,
    "max": 600,
    "tickInterval": 50,
    "lineWidth": 3,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.y_axis = {
    "title": {"text": None},
    "labels": {"enabled": False},
    "gridLineWidth": 0,
    "min": 0,
    "max": 1.2,
    "visible": False,
    "plotLines": [{"value": 0, "width": 3, "color": INK_SOFT, "zIndex": 2}],
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.tooltip = {"enabled": False}

# Rug ticks: short vertical marks at axis edge (0 to 0.15 = 12.5% of y-range)
for v in sorted(values):
    tick_series = LineSeries()
    tick_series.data = [[float(v), 0], [float(v), 0.15]]
    tick_series.color = TICK_COLOR
    tick_series.line_width = 7
    tick_series.marker = {"enabled": False}
    tick_series.enable_mouse_tracking = False
    tick_series.states = {"hover": {"enabled": False}}
    tick_series.show_in_legend = False
    chart.add_series(tick_series)

# Download Highcharts JS (required for headless Chrome — CDN blocked on file://)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ width: 4800px; height: 2700px; overflow: hidden; background: {PAGE_BG}; }}
        #container {{ width: 4800px; height: 2700px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
