""" anyplot.ai
precision-recall: Precision-Recall Curve
Library: highcharts unknown | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-10
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

# Okabe-Ito palette
BRAND = "#009E73"  # First series (primary)
SECONDARY = "#954477"  # Baseline reference

# Data - simulate binary classification results
np.random.seed(42)
n_samples = 500

# Ground truth: imbalanced binary labels (30% positive class)
positive_ratio = 0.3
y_true = np.random.binomial(1, positive_ratio, n_samples)

# Predicted scores: realistic classifier output
y_scores = np.where(y_true == 1, np.random.beta(5, 2, n_samples), np.random.beta(2, 5, n_samples))

# Compute precision-recall curve - inlined for KISS principle
sorted_indices = np.argsort(y_scores)[::-1]
y_scores_sorted = y_scores[sorted_indices]
thresholds = np.unique(y_scores_sorted)[::-1]

precisions = []
recalls = []
total_positives = np.sum(y_true)

for threshold in thresholds:
    y_pred = (y_scores >= threshold).astype(int)
    tp = np.sum((y_pred == 1) & (y_true == 1))
    fp = np.sum((y_pred == 1) & (y_true == 0))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / total_positives if total_positives > 0 else 0.0
    precisions.append(precision)
    recalls.append(recall)

precisions.append(1.0)
recalls.append(0.0)

precision = np.array(precisions)
recall = np.array(recalls)

# Compute Average Precision using trapezoidal rule
sorted_indices = np.argsort(recall)
recall_sorted = recall[sorted_indices]
precision_sorted = precision[sorted_indices]

ap_score = 0.0
for i in range(1, len(recall_sorted)):
    ap_score += (recall_sorted[i] - recall_sorted[i - 1]) * (precision_sorted[i] + precision_sorted[i - 1]) / 2

# Prepare data for Highcharts
pr_data = list(zip(recall.tolist(), precision.tolist(), strict=False))

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart settings with theme-adaptive colors
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 250,
    "marginLeft": 200,
    "marginRight": 120,
    "marginTop": 150,
}

# Title
chart.options.title = {
    "text": "precision-recall · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "bold", "color": INK},
    "y": 60,
}

# Subtitle showing AP score
chart.options.subtitle = {
    "text": f"Average Precision (AP) = {ap_score:.3f}",
    "style": {"fontSize": "22px", "color": INK_SOFT},
    "y": 100,
}

# X-axis (Recall) with theme-adaptive colors
chart.options.x_axis = {
    "title": {"text": "Recall (Sensitivity)", "style": {"fontSize": "22px", "color": INK}, "margin": 30},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.1,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineWidth": 2,
    "lineColor": INK_SOFT,
}

# Y-axis (Precision) with theme-adaptive colors
chart.options.y_axis = {
    "title": {
        "text": "Precision (Positive Predictive Value)",
        "style": {"fontSize": "22px", "color": INK},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.1,
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "lineWidth": 2,
    "lineColor": INK_SOFT,
}

# Legend with theme-adaptive colors
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 120,
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "padding": 20,
}

# Precision-Recall curve as area series (Okabe-Ito brand color)
pr_series = AreaSeries()
pr_series.name = f"Classifier (AP = {ap_score:.3f})"
pr_series.data = pr_data
pr_series.color = BRAND
pr_series.fill_opacity = 0.3
pr_series.line_width = 4
pr_series.step = "left"
pr_series.marker = {"enabled": False}

chart.add_series(pr_series)

# Baseline: random classifier (horizontal line at positive class ratio)
baseline_data = [[0, positive_ratio], [1, positive_ratio]]
baseline_series = SplineSeries()
baseline_series.name = f"Random Baseline (ratio = {positive_ratio:.2f})"
baseline_series.data = baseline_data
baseline_series.color = SECONDARY
baseline_series.line_width = 3
baseline_series.dash_style = "Dash"
baseline_series.marker = {"enabled": False}

chart.add_series(baseline_series)

# Plot options
chart.options.plot_options = {
    "area": {"marker": {"enabled": False}, "lineWidth": 4, "step": "left"},
    "line": {"marker": {"enabled": False}, "lineWidth": 3},
    "series": {"animation": False},
}

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS from jsDelivr CDN
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts/highcharts.js"
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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive viewing
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
time.sleep(5)

driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
