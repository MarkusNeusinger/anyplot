""" pyplots.ai
precision-recall: Precision-Recall Curve
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
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - simulate binary classification results
np.random.seed(42)
n_samples = 500

# Ground truth: imbalanced binary labels (30% positive class)
positive_ratio = 0.3
y_true = np.random.binomial(1, positive_ratio, n_samples)

# Predicted scores: realistic classifier output (correlated with true labels)
# Good classifier: higher scores for positive class
y_scores = np.where(
    y_true == 1,
    np.random.beta(5, 2, n_samples),  # Higher scores for positives
    np.random.beta(2, 5, n_samples),  # Lower scores for negatives
)


# Compute precision-recall curve (manual implementation)
def compute_precision_recall_curve(y_true, y_scores):
    """Compute precision-recall pairs for different probability thresholds."""
    # Sort by decreasing score
    sorted_indices = np.argsort(y_scores)[::-1]
    y_scores_sorted = y_scores[sorted_indices]

    # Get unique thresholds
    thresholds = np.unique(y_scores_sorted)[::-1]

    precisions = []
    recalls = []

    total_positives = np.sum(y_true)

    for threshold in thresholds:
        # Predictions at this threshold
        y_pred = (y_scores >= threshold).astype(int)

        # True positives and false positives
        tp = np.sum((y_pred == 1) & (y_true == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))

        # Precision and recall
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / total_positives if total_positives > 0 else 0.0

        precisions.append(precision)
        recalls.append(recall)

    # Add endpoint (recall=0, precision=1)
    precisions.append(1.0)
    recalls.append(0.0)

    return np.array(precisions), np.array(recalls), thresholds


def compute_average_precision(precision, recall):
    """Compute Average Precision using the trapezoidal rule."""
    # Sort by recall (ascending)
    sorted_indices = np.argsort(recall)
    recall_sorted = recall[sorted_indices]
    precision_sorted = precision[sorted_indices]

    # Compute AP as area under the curve using manual trapezoidal integration
    # (np.trapz deprecated in NumPy 2.0+)
    ap = 0.0
    for i in range(1, len(recall_sorted)):
        ap += (recall_sorted[i] - recall_sorted[i - 1]) * (precision_sorted[i] + precision_sorted[i - 1]) / 2
    return ap


precision, recall, thresholds = compute_precision_recall_curve(y_true, y_scores)

# Average Precision score
ap_score = compute_average_precision(precision, recall)

# Prepare data for Highcharts (stepped line representation)
# Use recall as x, precision as y - data should go from recall=1 to recall=0
pr_data = list(zip(recall.tolist(), precision.tolist(), strict=False))

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 200,
    "marginRight": 120,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "precision-recall · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
    "y": 60,
}

# Subtitle showing AP score
chart.options.subtitle = {
    "text": f"Average Precision (AP) = {ap_score:.3f}",
    "style": {"fontSize": "32px", "color": "#666666"},
    "y": 100,
}

# X-axis (Recall)
chart.options.x_axis = {
    "title": {"text": "Recall (Sensitivity)", "style": {"fontSize": "36px", "fontWeight": "bold"}, "margin": 30},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.1,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Y-axis (Precision)
chart.options.y_axis = {
    "title": {
        "text": "Precision (Positive Predictive Value)",
        "style": {"fontSize": "36px", "fontWeight": "bold"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.1,
    "gridLineWidth": 1,
    "gridLineColor": "#e0e0e0",
    "lineWidth": 2,
    "lineColor": "#333333",
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 120,
    "backgroundColor": "rgba(255, 255, 255, 0.9)",
    "borderWidth": 1,
    "borderColor": "#cccccc",
    "padding": 20,
}

# Precision-Recall curve as area series
pr_series = AreaSeries()
pr_series.name = f"Classifier (AP = {ap_score:.3f})"
pr_series.data = pr_data
pr_series.color = "#306998"
pr_series.fill_opacity = 0.3
pr_series.line_width = 4
pr_series.step = "left"  # Stepped line for PR curve
pr_series.marker = {"enabled": False}

chart.add_series(pr_series)

# Baseline: random classifier (horizontal line at positive class ratio)
baseline_data = [[0, positive_ratio], [1, positive_ratio]]
baseline_series = ScatterSeries()
baseline_series.name = f"Random Baseline (ratio = {positive_ratio:.2f})"
baseline_series.data = baseline_data
baseline_series.color = "#FFD43B"
baseline_series.line_width = 3
baseline_series.dash_style = "Dash"
baseline_series.marker = {"enabled": False}
baseline_series.type = "line"

chart.add_series(baseline_series)

# Plot options
chart.options.plot_options = {
    "area": {"marker": {"enabled": False}, "lineWidth": 4, "step": "left"},
    "line": {"marker": {"enabled": False}, "lineWidth": 3},
    "series": {"animation": False},
}

# Credits
chart.options.credits = {"enabled": False}

# Export to PNG via Selenium
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate JavaScript literal
html_str = chart.to_js_literal()

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive viewing
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
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.set_window_size(4800, 2800)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

# Take screenshot of just the chart container
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
