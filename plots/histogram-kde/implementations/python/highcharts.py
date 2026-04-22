""" pyplots.ai
histogram-kde: Histogram with KDE Overlay
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaSplineSeries
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Simulated stock returns with realistic distribution
np.random.seed(42)
# Mix of normal returns with some fat tails (bimodal for visual interest)
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
# Vectorized KDE: for each x, sum Gaussian contributions from all data points
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
    "backgroundColor": "#ffffff",
    "marginBottom": 300,
    "marginLeft": 200,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "histogram-kde · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
}

chart.options.subtitle = {
    "text": "Simulated Daily Stock Returns (%)",
    "style": {"fontSize": "44px", "color": "#666666"},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Return (%)", "style": {"fontSize": "48px"}, "offset": 60},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "tickLength": 15,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Density", "style": {"fontSize": "48px"}, "margin": 30},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "40px"},
    "symbolRadius": 0,
    "symbolWidth": 50,
    "symbolHeight": 30,
    "align": "right",
    "verticalAlign": "top",
    "x": -50,
    "y": 80,
}

# Plot options
chart.options.plot_options = {
    "column": {"pointPadding": 0, "groupPadding": 0, "borderWidth": 1, "borderColor": "#1e4f7a"},
    "areaspline": {"lineWidth": 6, "marker": {"enabled": False}},
}

# Histogram series (column chart)
histogram_series = ColumnSeries()
histogram_series.name = "Histogram"
histogram_series.data = [{"x": float(bc), "y": float(c)} for bc, c in zip(bin_centers, counts, strict=True)]
histogram_series.color = "rgba(48, 105, 152, 0.6)"  # Python Blue with transparency
histogram_series.point_width = int(bin_width * 280)  # Scale bar width for visibility

chart.add_series(histogram_series)

# KDE series (area spline for smooth curve)
kde_series = AreaSplineSeries()
kde_series.name = "KDE"
kde_series.data = [[float(x), float(y)] for x, y in zip(x_kde, y_kde, strict=True)]
kde_series.color = "#FFD43B"  # Python Yellow
kde_series.fill_opacity = 0.2
kde_series.line_width = 6

chart.add_series(kde_series)

# Download Highcharts JS for inline embedding (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate JavaScript literal
js_literal = chart.to_js_literal()

# Create HTML with inline script
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{js_literal}</script>
</body>
</html>"""

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
