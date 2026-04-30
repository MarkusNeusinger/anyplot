""" anyplot.ai
ridgeline-basic: Basic Ridgeline Plot
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-04-30
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
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - monthly temperature distributions (°C) showing seasonal patterns
np.random.seed(42)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

month_params = {
    "Jan": (2, 4),
    "Feb": (4, 4),
    "Mar": (8, 5),
    "Apr": (12, 5),
    "May": (17, 5),
    "Jun": (21, 4),
    "Jul": (24, 3),
    "Aug": (23, 3),
    "Sep": (19, 4),
    "Oct": (14, 5),
    "Nov": (8, 5),
    "Dec": (4, 4),
}

x_min, x_max = -10, 35
x_grid = np.linspace(x_min, x_max, 300)

# KDE for each month via scipy (no custom function needed)
ridge_data = []
for i, month in enumerate(months):
    mean, std = month_params[month]
    samples = np.random.normal(mean, std, 200)
    kde = stats.gaussian_kde(samples)
    ridge_data.append({"month": month, "index": i, "density": kde(x_grid)})

# Normalize densities; ridge_scale=1.8 gives ~50% overlap between adjacent ridges
max_density = max(r["density"].max() for r in ridge_data)
ridge_scale = 1.8

# Viridis colors sampled at 12 evenly-spaced positions (purple=cold, yellow=warm)
MONTH_COLORS = [
    "#440154",  # Jan - deep purple
    "#482677",  # Feb
    "#3f4788",  # Mar
    "#31688e",  # Apr
    "#26828e",  # May
    "#1f9e89",  # Jun
    "#35b779",  # Jul
    "#6dcd59",  # Aug
    "#b4de2c",  # Sep
    "#dce319",  # Oct
    "#fbe723",  # Nov
    "#fde725",  # Dec - bright yellow
]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 220,
    "marginLeft": 320,
    "marginRight": 100,
    "marginTop": 160,
}

chart.options.title = {
    "text": "ridgeline-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": INK},
}

chart.options.x_axis = {
    "title": {"text": "Temperature (°C)", "style": {"fontSize": "48px", "color": INK}},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "min": x_min,
    "max": x_max,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "tickInterval": 5,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
}

chart.options.y_axis = {
    "title": {"enabled": False},
    "labels": {
        "style": {"fontSize": "36px", "color": INK_SOFT},
        "formatter": """function() {
            var months = ['Jan','Feb','Mar','Apr','May','Jun',
                          'Jul','Aug','Sep','Oct','Nov','Dec'];
            var idx = Math.round(this.value);
            if (idx >= 0 && idx < months.length) { return months[idx]; }
            return '';
        }""",
    },
    "tickPositions": list(range(12)),
    "gridLineWidth": 0,
    "min": -0.8,
    "max": 13.5,
    "lineColor": INK_SOFT,
}

chart.options.legend = {"enabled": False}

chart.options.plot_options = {
    "area": {"fillOpacity": 0.7, "lineWidth": 3, "marker": {"enabled": False}, "enableMouseTracking": False}
}

chart.options.credits = {"enabled": False}

# Add ridges — December first (drawn behind), January last (drawn in front)
for i in range(len(months) - 1, -1, -1):
    r = ridge_data[i]
    base_y = float(i)
    scaled_density = (r["density"] / max_density) * ridge_scale

    area_data = [[float(x_val), float(base_y + d_val)] for x_val, d_val in zip(x_grid, scaled_density, strict=True)]

    color = MONTH_COLORS[i]
    series = AreaSeries()
    series.data = area_data
    series.name = months[i]
    series.color = color
    series.fill_color = {
        "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
        "stops": [[0, color + "cc"], [1, color + "22"]],
    }
    series.threshold = base_y
    chart.add_series(series)

# Download Highcharts JS (cache to /tmp for reruns)
cache_path = Path("/tmp/highcharts.js")
if cache_path.exists() and cache_path.stat().st_size > 1000:
    highcharts_js = cache_path.read_text(encoding="utf-8")
else:
    hc_url = "https://cdn.jsdelivr.net/npm/highcharts@11.4.8/highcharts.js"
    with urllib.request.urlopen(hc_url, timeout=30) as resp:
        highcharts_js = resp.read().decode("utf-8")
    cache_path.write_text(highcharts_js, encoding="utf-8")

# Build self-contained HTML with inline JS
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

# Screenshot via Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
