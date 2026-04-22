""" pyplots.ai
pdp-basic: Partial Dependence Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries, LineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import make_regression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Data - Train a GradientBoostingRegressor and compute partial dependence
np.random.seed(42)
X, y = make_regression(n_samples=500, n_features=5, n_informative=3, noise=20, random_state=42)

# Train model
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, y)

# Compute partial dependence for feature 0 (most informative)
feature_idx = 0
pd_results = partial_dependence(model, X, features=[feature_idx], kind="average", grid_resolution=80)
feature_values = pd_results["grid_values"][0]
avg_predictions = pd_results["average"][0]

# Compute individual conditional expectations for confidence band
individual_pd = partial_dependence(model, X, features=[feature_idx], kind="individual", grid_resolution=80)
individual_preds = individual_pd["individual"][0]

# Center at zero for easier interpretation
avg_predictions = avg_predictions - np.mean(avg_predictions)
individual_preds = individual_preds - np.mean(individual_preds, axis=1, keepdims=True)

# Compute confidence intervals (5th and 95th percentile across samples)
lower_bound = np.percentile(individual_preds, 5, axis=0)
upper_bound = np.percentile(individual_preds, 95, axis=0)

# Subsample training data for rug plot
rug_sample_idx = np.random.choice(len(X), size=50, replace=False)
rug_values = X[rug_sample_idx, feature_idx]

# Create Highcharts chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {"type": "line", "width": 4800, "height": 2700, "backgroundColor": "#ffffff", "marginBottom": 200}

# Title
chart.options.title = {
    "text": "pdp-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {"text": "Partial Dependence of Feature 0 on Model Predictions", "style": {"fontSize": "32px"}}

# Axes
chart.options.x_axis = {
    "title": {"text": "Feature 0 Value", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "tickInterval": 0.5,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.1)",
    "plotLines": [
        {"value": float(rug_values[i]), "width": 3, "color": "rgba(48,105,152,0.4)", "zIndex": 1}
        for i in range(len(rug_values))
    ],
}

chart.options.y_axis = {
    "title": {"text": "Partial Dependence (centered)", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.15)",
    "plotLines": [{"value": 0, "width": 2, "color": "#888888", "dashStyle": "Dash", "zIndex": 2}],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -50,
    "y": 100,
    "itemStyle": {"fontSize": "28px"},
}

# Tooltip
chart.options.tooltip = {"shared": True, "valueDecimals": 2, "style": {"fontSize": "24px"}}

# Plot options
chart.options.plot_options = {
    "series": {"animation": False},
    "arearange": {"fillOpacity": 0.3, "lineWidth": 0},
    "line": {"lineWidth": 5},
}

# Add confidence band as arearange series
confidence_data = [
    [float(feature_values[i]), float(lower_bound[i]), float(upper_bound[i])] for i in range(len(feature_values))
]

confidence_series = AreaRangeSeries()
confidence_series.data = confidence_data
confidence_series.name = "90% Confidence Interval"
confidence_series.color = "rgba(48,105,152,0.25)"
confidence_series.fill_opacity = 0.25
chart.add_series(confidence_series)

# Add main PDP line
pdp_data = [[float(feature_values[i]), float(avg_predictions[i])] for i in range(len(feature_values))]

pdp_series = LineSeries()
pdp_series.data = pdp_data
pdp_series.name = "Partial Dependence"
pdp_series.color = "#306998"  # Python Blue
pdp_series.marker = {"enabled": False}
chart.add_series(pdp_series)

# Export to PNG via Selenium
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

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
