""" anyplot.ai
gain-curve: Cumulative Gains Chart
Library: highcharts unknown | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-11
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
from highcharts_core.options.series.spline import SplineSeries
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
ACCENT = "#C475FD"  # Okabe-Ito position 2 for baseline

# Data: Customer response model with predicted probabilities
np.random.seed(42)
n_samples = 1000

# Simulate a classification model with varying discrimination
# Create a mix of strong and weak signals
positive_rate = 0.15  # 15% positive class
n_positives = int(n_samples * positive_rate)
n_negatives = n_samples - n_positives

# Generate predicted probabilities
# Positives tend to have higher scores, but with overlap
positive_scores = np.random.beta(5, 2, n_positives)  # Higher scores
negative_scores = np.random.beta(2, 5, n_negatives)  # Lower scores

y_true = np.concatenate([np.ones(n_positives), np.zeros(n_negatives)])
y_score = np.concatenate([positive_scores, negative_scores])

# Calculate gain curve
sorted_indices = np.argsort(y_score)[::-1]  # Sort by score descending
sorted_true = y_true[sorted_indices]

# Cumulative gains
cumulative_positives = np.cumsum(sorted_true)
total_positives = cumulative_positives[-1]
gains = cumulative_positives / total_positives * 100

# Population percentages
population_pct = np.arange(1, n_samples + 1) / n_samples * 100

# Subsample for smoother chart display
sample_indices = np.linspace(0, len(population_pct) - 1, 100, dtype=int)
x_values = population_pct[sample_indices].tolist()
y_values = gains[sample_indices].tolist()

# Add starting point
x_values = [0] + x_values
y_values = [0] + y_values

# Random baseline (diagonal)
baseline_x = [0, 100]
baseline_y = [0, 100]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 350,
    "marginLeft": 220,
    "marginTop": 180,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "gain-curve · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
}

# Subtitle
chart.options.subtitle = {
    "text": "Customer Response Model Performance",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Population Targeted (%)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Positive Cases Captured (%)", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "min": 0,
    "max": 100,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
}

# Legend positioned at top-left to avoid overlap
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "layout": "vertical",
    "align": "left",
    "verticalAlign": "top",
    "x": 80,
    "y": 60,
    "symbolWidth": 32,
    "symbolHeight": 16,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 16,
}

# Plot options
chart.options.plot_options = {
    "area": {"lineWidth": 4, "marker": {"enabled": False}},
    "line": {"lineWidth": 4, "marker": {"enabled": False}},
}

# Model gain curve with area fill
gain_series = AreaSeries()
gain_series.data = [[x, y] for x, y in zip(x_values, y_values, strict=True)]
gain_series.name = "Model Gain"
gain_series.color = BRAND
gain_series.fill_color = {
    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
    "stops": [[0, "rgba(0, 158, 115, 0.5)"], [1, "rgba(0, 158, 115, 0.1)"]],
}
chart.add_series(gain_series)

# Random baseline (dashed diagonal)
baseline_series = SplineSeries()
baseline_series.data = [[x, y] for x, y in zip(baseline_x, baseline_y, strict=True)]
baseline_series.name = "Random Selection"
baseline_series.color = ACCENT
baseline_series.dash_style = "Dash"
chart.add_series(baseline_series)

# Tooltip
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{series.name}</b><br/>Population: {point.x:.1f}%<br/>Captured: {point.y:.1f}%",
    "style": {"fontSize": "18px"},
}

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
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

# Save HTML artifact for both themes
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
