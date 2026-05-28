""" anyplot.ai
histogram-kde: Histogram with KDE Overlay
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-06
"""

import os
import tempfile
import time
from pathlib import Path

import numpy as np
import requests
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSplineSeries
from highcharts_core.options.series.bar import ColumnSeries
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
SECONDARY = "#C475FD"  # Okabe-Ito position 2

# Data: Simulated stock returns with realistic distribution
np.random.seed(42)
returns_normal = np.random.normal(loc=0.05, scale=2.5, size=400)
returns_tail = np.random.normal(loc=-3.0, scale=1.5, size=100)
values = np.concatenate([returns_normal, returns_tail])

# Create histogram bins (density normalized)
n_bins = 30
counts, bin_edges = np.histogram(values, bins=n_bins, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]

# KDE calculation using Gaussian kernel (Scott's rule bandwidth)
n = len(values)
bandwidth = 1.06 * np.std(values) * n ** (-1 / 5)
x_kde = np.linspace(values.min() - 1, values.max() + 1, 200)
y_kde = np.array([np.sum(np.exp(-0.5 * ((x - values) / bandwidth) ** 2)) for x in x_kde])
y_kde /= n * bandwidth * np.sqrt(2 * np.pi)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 300,
    "marginLeft": 250,
    "marginTop": 200,
    "marginRight": 200,
}

# Title and subtitle with enhanced typography hierarchy
chart.options.title = {
    "text": "histogram-kde · highcharts · anyplot.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": INK, "letterSpacing": "2px"},
    "margin": 30,
}

chart.options.subtitle = {
    "text": "Simulated Daily Stock Returns (%)",
    "style": {"fontSize": "44px", "color": INK_SOFT, "fontWeight": "500"},
    "margin": 15,
}

# X-axis with enhanced styling
chart.options.x_axis = {
    "title": {"text": "Return (%)", "style": {"fontSize": "48px", "color": INK, "fontWeight": "600"}, "offset": 80},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 0,
    "tickLength": 15,
}

# Y-axis with enhanced grid styling
chart.options.y_axis = {
    "title": {"text": "Density", "style": {"fontSize": "48px", "color": INK, "fontWeight": "600"}, "margin": 40},
    "labels": {"style": {"fontSize": "36px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
}

# Legend - integrated with translucent styling for sophistication
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px", "color": INK_SOFT, "fontWeight": "500"},
    "symbolRadius": 2,
    "symbolWidth": 50,
    "symbolHeight": 30,
    "align": "right",
    "verticalAlign": "top",
    "x": -80,
    "y": 120,
    "backgroundColor": f"rgba({int(ELEVATED_BG[1:3], 16)}, {int(ELEVATED_BG[3:5], 16)}, {int(ELEVATED_BG[5:7], 16)}, 0.85)",
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "borderRadius": 4,
    "padding": 20,
    "margin": 10,
}

# Plot options with enhanced styling
chart.options.plot_options = {
    "column": {"pointPadding": 0, "groupPadding": 0, "borderWidth": 1, "borderColor": BRAND, "stacking": None},
    "areaspline": {"lineWidth": 6, "marker": {"enabled": False}, "states": {"hover": {"lineWidth": 8}}},
}

# Histogram series (column chart) - first series in Okabe-Ito brand color
histogram_series = ColumnSeries()
histogram_series.name = "Histogram"
histogram_series.data = [{"x": float(bc), "y": float(c)} for bc, c in zip(bin_centers, counts, strict=True)]
histogram_series.color = f"rgba({int('00', 16)}, {int('9E', 16)}, {int('73', 16)}, 0.55)"
histogram_series.point_width = int(bin_width * 280)
histogram_series.states = {
    "hover": {"color": f"rgba({int('00', 16)}, {int('9E', 16)}, {int('73', 16)}, 0.75)", "borderWidth": 2}
}

chart.add_series(histogram_series)

# KDE series (area spline for smooth curve) - second series in secondary color
kde_series = AreaSplineSeries()
kde_series.name = "KDE"
kde_series.data = [[float(x), float(y)] for x, y in zip(x_kde, y_kde, strict=True)]
kde_series.color = SECONDARY
kde_series.fill_opacity = 0.15
kde_series.line_width = 7
kde_series.states = {"hover": {"fillOpacity": 0.25, "lineWidth": 9}}

chart.add_series(kde_series)

# Download Highcharts JS for inline embedding
# Try multiple CDN sources
urls = ["https://cdn.jsdelivr.net/npm/highcharts@11.4.0/highcharts.min.js", "https://code.highcharts.com/highcharts.js"]

highcharts_js = None
for url in urls:
    try:
        response = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=30
        )
        response.raise_for_status()
        highcharts_js = response.text
        break
    except Exception:
        continue

if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from all CDN sources")

# Generate JavaScript literal
js_literal = chart.to_js_literal()

# Create HTML with inline script
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Save HTML file
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
