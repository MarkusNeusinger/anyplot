""" pyplots.ai
roc-curve: ROC Curve with AUC
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

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


# Data - simulate ROC curve from a binary classifier
np.random.seed(42)

# Generate synthetic prediction scores and true labels
n_samples = 500
y_true = np.concatenate([np.zeros(250), np.ones(250)])
# Good classifier: positive class has higher scores
y_scores = np.concatenate(
    [
        np.random.beta(2, 5, 250),  # Negative class - lower scores
        np.random.beta(5, 2, 250),  # Positive class - higher scores
    ]
)

# Compute ROC curve manually
thresholds = np.linspace(0, 1, 200)
fpr_list = []
tpr_list = []
for thresh in thresholds:
    predictions = (y_scores >= thresh).astype(int)
    tp = np.sum((predictions == 1) & (y_true == 1))
    fp = np.sum((predictions == 1) & (y_true == 0))
    tn = np.sum((predictions == 0) & (y_true == 0))
    fn = np.sum((predictions == 0) & (y_true == 1))
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fpr_list.append(fpr)
    tpr_list.append(tpr)

fpr = np.array(fpr_list)
tpr = np.array(tpr_list)

# Sort by FPR for proper curve plotting
sorted_indices = np.argsort(fpr)
fpr = fpr[sorted_indices]
tpr = tpr[sorted_indices]

# Calculate AUC using trapezoidal rule
auc = np.trapezoid(tpr, fpr)

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 canvas
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 250,
    "marginTop": 200,
    "marginRight": 150,
}

# Title
chart.options.title = {
    "text": "roc-curve · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle with AUC
chart.options.subtitle = {"text": "Binary Classifier Performance", "style": {"fontSize": "32px"}}

# X-axis configuration
chart.options.x_axis = {
    "title": {"text": "False Positive Rate", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.2,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Y-axis configuration
chart.options.y_axis = {
    "title": {"text": "True Positive Rate", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.2,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Legend configuration - position in bottom-right of plot area
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "bottom",
    "layout": "vertical",
    "floating": True,
    "x": -150,
    "y": -150,
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
    "area": {"fillOpacity": 0.3, "lineWidth": 6, "marker": {"enabled": False}},
    "spline": {"lineWidth": 5, "dashStyle": "Dash", "marker": {"enabled": False}},
}

# ROC Curve series (area under curve)
roc_data = [[float(x), float(y)] for x, y in zip(fpr, tpr, strict=True)]
roc_series = AreaSeries()
roc_series.data = roc_data
roc_series.name = f"ROC Curve (AUC = {auc:.3f})"
roc_series.color = "#306998"  # Python Blue
roc_series.fill_color = {
    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
    "stops": [[0, "rgba(48, 105, 152, 0.5)"], [1, "rgba(48, 105, 152, 0.1)"]],
}
chart.add_series(roc_series)

# Random classifier reference line (diagonal)
diagonal_data = [[0, 0], [1, 1]]
diagonal_series = SplineSeries()
diagonal_series.data = diagonal_data
diagonal_series.name = "Random Classifier (AUC = 0.5)"
diagonal_series.color = "#8B8000"  # Dark yellow/olive for visibility on white
diagonal_series.dash_style = "ShortDash"
diagonal_series.line_width = 5
chart.add_series(diagonal_series)

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
