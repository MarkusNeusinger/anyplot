"""anyplot.ai
roc-curve: ROC Curve with AUC
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-05-09
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


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"
NEUTRAL = "#1A1A1A" if THEME == "light" else "#E8E8E0"

# Data - simulate ROC curve from a binary classifier
np.random.seed(42)

n_samples = 500
y_true = np.concatenate([np.zeros(250), np.ones(250)])
y_scores = np.concatenate([np.random.beta(2, 5, 250), np.random.beta(5, 2, 250)])

# Compute ROC curve
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

sorted_indices = np.argsort(fpr)
fpr = fpr[sorted_indices]
tpr = tpr[sorted_indices]

auc = np.trapezoid(tpr, fpr)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for theme-adaptive rendering
chart.options.chart = {
    "type": "area",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginBottom": 280,
    "marginLeft": 280,
    "marginTop": 200,
    "marginRight": 180,
}

# Title
chart.options.title = {
    "text": "roc-curve · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "medium", "color": INK},
}

# X-axis
chart.options.x_axis = {
    "title": {"text": "False Positive Rate", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.2,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "True Positive Rate", "style": {"fontSize": "22px", "color": INK}},
    "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
    "min": 0,
    "max": 1,
    "tickInterval": 0.2,
    "lineColor": INK_SOFT,
    "tickColor": INK_SOFT,
    "gridLineColor": GRID,
    "gridLineWidth": 1,
}

# Legend with improved positioning to avoid overlap
chart.options.legend = {
    "enabled": True,
    "align": "left",
    "verticalAlign": "bottom",
    "layout": "vertical",
    "floating": True,
    "x": 120,
    "y": -120,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "padding": 16,
    "itemStyle": {"fontSize": "18px", "color": INK_SOFT},
    "symbolRadius": 0,
    "symbolWidth": 40,
    "symbolHeight": 4,
}

# Plot options for larger elements
chart.options.plot_options = {
    "area": {"fillOpacity": 0.2, "lineWidth": 4, "marker": {"enabled": False}},
    "spline": {"lineWidth": 3, "dashStyle": "Dash", "marker": {"enabled": False}},
}

# Tooltip for better interactivity
chart.options.tooltip = {
    "enabled": True,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "style": {"fontSize": "16px", "color": INK},
    "headerFormat": "<b>Threshold point</b><br>",
    "pointFormat": "FPR: {point.x:.3f}<br>TPR: {point.y:.3f}<br>",
}

# ROC Curve series - using Okabe-Ito color
roc_data = [[float(x), float(y)] for x, y in zip(fpr, tpr, strict=True)]
roc_series = AreaSeries()
roc_series.data = roc_data
roc_series.name = f"ROC Curve (AUC = {auc:.3f})"
roc_series.color = BRAND
roc_series.fill_color = {
    "linearGradient": {"x1": 0, "y1": 0, "x2": 0, "y2": 1},
    "stops": [[0, "rgba(0, 158, 115, 0.4)"], [1, "rgba(0, 158, 115, 0.05)"]],
}
chart.add_series(roc_series)

# Random classifier reference line
diagonal_data = [[0, 0], [1, 1]]
diagonal_series = SplineSeries()
diagonal_series.data = diagonal_data
diagonal_series.name = "Random Classifier (AUC = 0.5)"
diagonal_series.color = NEUTRAL
diagonal_series.dash_style = "Dash"
diagonal_series.line_width = 3
chart.add_series(diagonal_series)

# Download Highcharts JS from CDN
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11.1.0/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
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

# Save HTML
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()
