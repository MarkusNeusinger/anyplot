"""anyplot.ai
sparkline-basic: Basic Sparkline
Library: highcharts_core 2.x | Python 3.13.11
Quality: 87/100 | Updated: 2026-05-02
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Okabe-Ito categorical palette — identical across themes; only chrome flips.
LINE_COLOR = "#009E73"
FILL_COLOR_RGBA = "rgba(0, 158, 115, 0.18)"
MIN_COLOR = "#D55E00"
MAX_COLOR = "#0072B2"

# Data — 30 trading days of daily closing prices for a hypothetical mid-cap
# stock. Geometric random walk with mild positive drift, an earnings-week
# pullback near day 14, and a recovery into the back half. Picked from the
# spec's listed applications ("inline stock price trends embedded in
# financial tables or reports").
np.random.seed(7)
n_days = 30
day = np.arange(n_days)
log_returns = np.random.normal(loc=0.005, scale=0.022, size=n_days)
log_returns[12:16] -= 0.038  # earnings-week pullback
log_returns[20:25] += 0.020  # post-pullback rally
prices = 42.50 * np.exp(np.cumsum(log_returns))

min_idx = int(np.argmin(prices))
max_idx = int(np.argmax(prices))

# Anchor the y-axis to the data range with a small headroom so the line
# variation fills most of the canvas (otherwise the area fill dominates
# and the trend is unreadable).
y_span = float(prices.max() - prices.min())
y_min = float(prices.min() - y_span * 0.20)
y_max = float(prices.max() + y_span * 0.15)

# Wider, shorter canvas — inline-cell sparklines lean more like 6:1 than 4:1
CANVAS_W, CANVAS_H = 4800, 800

chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "area",
    "width": CANVAS_W,
    "height": CANVAS_H,
    "backgroundColor": PAGE_BG,
    "spacing": [50, 100, 50, 100],
    "style": {"color": INK, "fontFamily": "-apple-system, system-ui, sans-serif"},
}

chart.options.title = {
    "text": "sparkline-basic · highcharts · anyplot.ai",
    "align": "center",
    "style": {"fontSize": "30px", "color": INK, "fontWeight": "bold"},
}

# Sparkline minimalism — no axes/grid/legend; padding so extreme markers stay on canvas
chart.options.x_axis = {"visible": False, "minPadding": 0.02, "maxPadding": 0.02}
chart.options.y_axis = {"visible": False, "gridLineWidth": 0, "min": y_min, "max": y_max}
chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}
chart.options.plot_options = {
    "series": {"animation": False, "enableMouseTracking": False, "states": {"hover": {"enabled": False}}},
    "area": {
        "fillColor": FILL_COLOR_RGBA,
        "lineColor": LINE_COLOR,
        "lineWidth": 4,
        "marker": {"enabled": False},
        "threshold": None,  # fill from line down to y_axis min, not to zero
    },
}

area = AreaSeries()
area.data = list(zip(day.tolist(), prices.tolist(), strict=True))
area.name = "Close"
chart.add_series(area)

min_marker = ScatterSeries()
min_marker.data = [[min_idx, float(prices[min_idx])]]
min_marker.name = "Low"
min_marker.color = MIN_COLOR
min_marker.marker = {"enabled": True, "radius": 22, "symbol": "circle"}
chart.add_series(min_marker)

max_marker = ScatterSeries()
max_marker.data = [[max_idx, float(prices[max_idx])]]
max_marker.name = "High"
max_marker.color = MAX_COLOR
max_marker.marker = {"enabled": True, "radius": 22, "symbol": "circle"}
chart.add_series(max_marker)

# Headless Chrome cannot load CDN scripts from file://, so embed Highcharts JS inline.
# (Highcharts' own CDN is rate-limited from cloud runners; jsdelivr mirrors the npm package.)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

js_literal = chart.to_js_literal()
html_inline = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:{CANVAS_W}px; height:{CANVAS_H}px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Site artifact — uses CDN link so served pages stay small.
html_cdn = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"></script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width:100%; height:100vh;"></div>
    <script>{js_literal}</script>
</body>
</html>"""
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_cdn)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_inline)
    temp_path = f.name

# Make the browser viewport bigger than the chart so headless chrome's
# top toolbar doesn't clip the bottom of the screenshot.
WINDOW_W = CANVAS_W
WINDOW_H = CANVAS_H + 200

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(f"--window-size={WINDOW_W},{WINDOW_H}")
chrome_options.add_argument("--hide-scrollbars")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(WINDOW_W, WINDOW_H)
driver.get(f"file://{temp_path}")
time.sleep(5)
container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
