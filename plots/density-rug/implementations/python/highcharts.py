""" anyplot.ai
density-rug: Density Plot with Rug Marks
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
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
from scipy.stats import gaussian_kde
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - Response times (in milliseconds) for a web service
np.random.seed(42)
# Bimodal distribution to show KDE's ability to reveal multiple modes
fast_responses = np.random.normal(120, 25, 80)
slow_responses = np.random.normal(280, 40, 45)
values = np.concatenate([fast_responses, slow_responses])
values = values[values > 0]  # Ensure positive response times

# Compute KDE
kde = gaussian_kde(values, bw_method=0.2)
x_range = np.linspace(values.min() - 20, values.max() + 20, 300)
density = kde(x_range)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
chart.options.chart = {
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "Arial, sans-serif", "color": INK},
    "marginBottom": 200,
    "marginLeft": 160,
}

# Title
chart.options.title = {
    "text": "density-rug · Python · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# Subtitle
chart.options.subtitle = {
    "text": "API Response Time Distribution (ms)",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Response Time (ms)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "min": float(x_range.min()),
    "max": float(x_range.max()),
    "tickInterval": 50,
}

# Y-axis - extend minimum to show rug marks below 0
rug_y_position = -max(density) * 0.08
chart.options.y_axis = {
    "title": {"text": "Density", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "min": rug_y_position * 1.5,  # Allow space for rug marks
    "plotLines": [{"value": 0, "color": INK_SOFT, "width": 2, "zIndex": 3}],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "verticalAlign": "top",
    "align": "right",
    "floating": True,
    "y": 60,
}

# Credits off
chart.options.credits = {"enabled": False}

# KDE density curve (Area series with fill) - using Okabe-Ito brand color
kde_series = AreaSeries()
kde_series.name = "Density (KDE)"
kde_series.data = [[float(x), float(y)] for x, y in zip(x_range, density, strict=True)]
kde_series.color = BRAND
kde_series.fill_opacity = 0.4
kde_series.line_width = 3

chart.add_series(kde_series)

# Rug marks - scatter points at the bottom using secondary Okabe-Ito color
rug_series = ScatterSeries()
rug_series.name = "Rug (Individual Points)"
rug_series.data = [[float(v), rug_y_position] for v in values]
rug_series.color = "#C475FD"  # Okabe-Ito position 2
rug_series.marker = {"symbol": "diamond", "radius": 8, "fillColor": "#C475FD", "lineWidth": 1, "lineColor": INK_SOFT}

chart.add_series(rug_series)

# Plot options
chart.options.plot_options = {
    "area": {"states": {"hover": {"enabled": False}}},
    "scatter": {"states": {"hover": {"enabled": False}}},
}

# Download Highcharts JS
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
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
<body style="margin:0; background-color: {PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG
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
