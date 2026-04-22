""" pyplots.ai
histogram-density: Density Histogram
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-29
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


# Data - Generate test score data with realistic distribution
np.random.seed(42)
values = np.random.normal(loc=75, scale=12, size=500)  # Test scores centered around 75

# Calculate density histogram
n_bins = 25
counts, bin_edges = np.histogram(values, bins=n_bins, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]

# Generate theoretical normal PDF for overlay (computed manually)
x_pdf = np.linspace(values.min() - 5, values.max() + 5, 200)
mean_val = np.mean(values)
std_val = np.std(values)
y_pdf = (1 / (std_val * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_pdf - mean_val) / std_val) ** 2)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 220,
    "marginLeft": 220,
    "marginRight": 100,
    "marginTop": 150,
    "spacingBottom": 30,
}

# Title
chart.options.title = {
    "text": "histogram-density · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle for context
chart.options.subtitle = {
    "text": "Test Score Distribution with Normal PDF Overlay",
    "style": {"fontSize": "32px", "color": "#666666"},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Test Score", "style": {"fontSize": "36px", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "28px"}},
    "lineWidth": 2,
    "tickWidth": 2,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Probability Density", "style": {"fontSize": "36px", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "gridLineDashStyle": "Dash",
    "min": 0,
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px", "fontWeight": "normal"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.9)",
    "borderWidth": 1,
    "borderColor": "#cccccc",
}

# Plot options
chart.options.plot_options = {
    "column": {"groupPadding": 0, "pointPadding": 0, "borderWidth": 1, "borderColor": "#1a4d73"},
    "areaspline": {"fillOpacity": 0.2, "lineWidth": 5, "marker": {"enabled": False}},
}

# Add histogram series (using column chart)
histogram_series = ColumnSeries()
histogram_series.name = "Empirical Density"
histogram_series.data = [[float(center), float(count)] for center, count in zip(bin_centers, counts, strict=True)]
histogram_series.color = "#306998"
histogram_series.point_width = bin_width * 35  # Adjust width for visibility

chart.add_series(histogram_series)

# Add theoretical PDF overlay as area spline
pdf_series = AreaSplineSeries()
pdf_series.name = "Normal PDF"
pdf_series.data = [[float(x), float(y)] for x, y in zip(x_pdf, y_pdf, strict=True)]
pdf_series.color = "#FFD43B"
pdf_series.fill_color = "rgba(255, 212, 59, 0.2)"
pdf_series.line_width = 5

chart.add_series(pdf_series)

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS
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

# Also save as plot.html for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    # For the HTML file, we can use CDN
    html_cdn = (
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>"""
        + html_str
        + """</script>
</body>
</html>"""
    )
    f.write(html_cdn)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
