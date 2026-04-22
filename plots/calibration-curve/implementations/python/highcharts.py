""" pyplots.ai
calibration-curve: Calibration Curve
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - simulate predictions from a binary classifier
np.random.seed(42)

n_samples = 2000
# Ground truth: balanced classes
y_true = np.concatenate([np.zeros(1000), np.ones(1000)])

# Simulated classifier that is slightly overconfident
# Positive class has higher predicted probabilities
y_prob = np.concatenate(
    [
        np.clip(np.random.beta(2, 5, 1000), 0, 1),  # Negative class - lower probs
        np.clip(np.random.beta(5, 2, 1000), 0, 1),  # Positive class - higher probs
    ]
)

# Shuffle data
shuffle_idx = np.random.permutation(n_samples)
y_true = y_true[shuffle_idx]
y_prob = y_prob[shuffle_idx]

# Compute calibration curve using 10 bins
n_bins = 10
bin_edges = np.linspace(0, 1, n_bins + 1)
bin_centers = []
fraction_of_positives = []
bin_counts = []

for i in range(n_bins):
    bin_mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
    if i == n_bins - 1:  # Include right edge for last bin
        bin_mask = (y_prob >= bin_edges[i]) & (y_prob <= bin_edges[i + 1])

    if np.sum(bin_mask) > 0:
        bin_centers.append((bin_edges[i] + bin_edges[i + 1]) / 2)
        fraction_of_positives.append(np.mean(y_true[bin_mask]))
        bin_counts.append(np.sum(bin_mask))

# Calculate Brier Score (mean squared error of probability predictions)
brier_score = np.mean((y_prob - y_true) ** 2)

# Calculate Expected Calibration Error (ECE)
ece = 0
total_samples = len(y_true)
for i in range(len(bin_centers)):
    weight = bin_counts[i] / total_samples
    ece += weight * abs(fraction_of_positives[i] - bin_centers[i])

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 canvas
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 280,
    "marginTop": 200,
    "marginRight": 400,
}

# Title
chart.options.title = {
    "text": "calibration-curve · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle with calibration metrics
chart.options.subtitle = {
    "text": f"Model Calibration Analysis | Brier Score: {brier_score:.4f} | ECE: {ece:.4f}",
    "style": {"fontSize": "32px"},
}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "Mean Predicted Probability", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "Fraction of Positives", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.1,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Legend configuration - positioned in bottom-right of plot area
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "bottom",
    "layout": "vertical",
    "floating": True,
    "x": -50,
    "y": -200,
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderWidth": 2,
    "borderColor": "#cccccc",
    "borderRadius": 5,
    "padding": 20,
    "itemStyle": {"fontSize": "28px"},
    "symbolRadius": 0,
    "symbolWidth": 50,
    "symbolHeight": 5,
}

# Plot options
chart.options.plot_options = {
    "scatter": {"marker": {"radius": 16, "symbol": "circle"}},
    "spline": {"lineWidth": 5, "marker": {"enabled": False}},
    "area": {"fillOpacity": 0.15, "lineWidth": 0, "marker": {"enabled": False}},
}

# Perfect calibration diagonal line
diagonal_data = [[0, 0], [1, 1]]
diagonal_series = SplineSeries()
diagonal_series.data = diagonal_data
diagonal_series.name = "Perfect Calibration"
diagonal_series.color = "#666666"
diagonal_series.dash_style = "ShortDash"
diagonal_series.line_width = 5
chart.add_series(diagonal_series)

# Calibration curve as line connecting the points
calibration_line_data = [[float(x), float(y)] for x, y in zip(bin_centers, fraction_of_positives, strict=True)]
calibration_line = SplineSeries()
calibration_line.data = calibration_line_data
calibration_line.name = f"Classifier (Brier: {brier_score:.3f})"
calibration_line.color = "#306998"  # Python Blue
calibration_line.line_width = 6
chart.add_series(calibration_line)

# Calibration curve points with larger markers
calibration_data = [
    {"x": float(x), "y": float(y), "z": count}
    for x, y, count in zip(bin_centers, fraction_of_positives, bin_counts, strict=True)
]
calibration_series = ScatterSeries()
calibration_series.data = calibration_data
calibration_series.name = "Calibration Points"
calibration_series.color = "#306998"  # Python Blue
calibration_series.marker = {"radius": 18, "symbol": "circle", "lineWidth": 3, "lineColor": "#ffffff"}
chart.add_series(calibration_series)


# Download Highcharts JS for inline embedding
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

# Save HTML file for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot with headless Chrome
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
