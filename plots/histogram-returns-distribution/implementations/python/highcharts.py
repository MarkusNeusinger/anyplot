""" pyplots.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-16
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.options.series.spline import SplineSeries
from scipy import stats
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Generate synthetic daily returns (252 trading days = 1 year)
np.random.seed(42)
n_days = 252
daily_returns = np.random.normal(loc=0.05, scale=1.2, size=n_days)  # Mean 0.05%, std 1.2%

# Calculate statistics
mean_return = np.mean(daily_returns)
std_return = np.std(daily_returns)
skewness = stats.skew(daily_returns)
kurtosis = stats.kurtosis(daily_returns)

# Create histogram bins for Highcharts
n_bins = 30
hist_counts, bin_edges = np.histogram(daily_returns, bins=n_bins, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

# Normal distribution overlay
x_norm = np.linspace(daily_returns.min() - 0.5, daily_returns.max() + 0.5, 100)
y_norm = stats.norm.pdf(x_norm, mean_return, std_return)

# Identify tail regions (beyond 2 standard deviations)
lower_tail = mean_return - 2 * std_return
upper_tail = mean_return + 2 * std_return

# Create histogram data with tail coloring
histogram_data = []
tail_data = []
for center, count in zip(bin_centers, hist_counts, strict=True):
    if center < lower_tail or center > upper_tail:
        tail_data.append({"x": float(center), "y": float(count)})
        histogram_data.append({"x": float(center), "y": 0})
    else:
        histogram_data.append({"x": float(center), "y": float(count)})
        tail_data.append({"x": float(center), "y": 0})

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 200,
    "marginRight": 200,
}

# Title
chart.options.title = {
    "text": "histogram-returns-distribution · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle with statistics
stats_text = (
    f"Mean: {mean_return:.2f}% | Std Dev: {std_return:.2f}% | Skewness: {skewness:.2f} | Kurtosis: {kurtosis:.2f}"
)
chart.options.subtitle = {"text": stats_text, "style": {"fontSize": "32px", "color": "#666666"}}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Daily Returns (%)", "style": {"fontSize": "42px"}},
    "labels": {"style": {"fontSize": "32px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Density", "style": {"fontSize": "42px"}},
    "labels": {"style": {"fontSize": "32px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
}

# Plot options
chart.options.plot_options = {
    "column": {"pointPadding": 0, "groupPadding": 0, "borderWidth": 1, "borderColor": "#ffffff"},
    "areaspline": {"fillOpacity": 0.0, "lineWidth": 5, "marker": {"enabled": False}},
}

# Credits
chart.options.credits = {"enabled": False}

# Add main histogram series
main_series = ColumnSeries()
main_series.name = "Returns Distribution"
main_series.data = histogram_data
main_series.color = "#306998"
main_series.point_width = int(4800 / n_bins * 0.85)
chart.add_series(main_series)

# Add tail series
tail_series = ColumnSeries()
tail_series.name = "Tail Regions (>2σ)"
tail_series.data = tail_data
tail_series.color = "#FFD43B"
tail_series.point_width = int(4800 / n_bins * 0.85)
chart.add_series(tail_series)

# Add normal distribution overlay
normal_series = SplineSeries()
normal_series.name = "Normal Distribution"
normal_series.data = [[float(x), float(y)] for x, y in zip(x_norm, y_norm, strict=True)]
normal_series.color = "#DC143C"
normal_series.line_width = 5
normal_series.marker = {"enabled": False}
chart.add_series(normal_series)

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

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot
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
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
