""" pyplots.ai
logistic-regression: Logistic Regression Curve Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import AreaRangeSeries
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.spline import SplineSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.linear_model import LogisticRegression


# Data - Generate binary classification data
np.random.seed(42)
n_points = 150

# Predictor: Study hours (0-10)
x = np.random.uniform(0, 10, n_points)

# Binary outcome: Pass/Fail (1/0) with logistic relationship
true_prob = 1 / (1 + np.exp(-1.5 * (x - 5)))
y = (np.random.random(n_points) < true_prob).astype(int)

# Fit logistic regression model
model = LogisticRegression()
model.fit(x.reshape(-1, 1), y)

# Generate smooth curve for plotting
x_curve = np.linspace(0, 10, 200)
y_prob = model.predict_proba(x_curve.reshape(-1, 1))[:, 1]

# Calculate confidence intervals using bootstrap
n_bootstrap = 100
bootstrap_probs = np.zeros((n_bootstrap, len(x_curve)))
for i in range(n_bootstrap):
    indices = np.random.choice(n_points, n_points, replace=True)
    x_boot, y_boot = x[indices], y[indices]
    model_boot = LogisticRegression()
    model_boot.fit(x_boot.reshape(-1, 1), y_boot)
    bootstrap_probs[i] = model_boot.predict_proba(x_curve.reshape(-1, 1))[:, 1]

ci_lower = np.percentile(bootstrap_probs, 2.5, axis=0)
ci_upper = np.percentile(bootstrap_probs, 97.5, axis=0)

# Jitter y values for visibility
jitter = np.random.uniform(-0.03, 0.03, n_points)
y_jittered = y + jitter

# Separate points by class
x_class0 = x[y == 0].tolist()
y_class0 = y_jittered[y == 0].tolist()
x_class1 = x[y == 1].tolist()
y_class1 = y_jittered[y == 1].tolist()

# Chart setup
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "style": {"fontFamily": "Arial, sans-serif"},
    "spacingBottom": 100,
    "spacingLeft": 50,
    "spacingTop": 50,
    "spacingRight": 50,
}

# Title
chart.options.title = {
    "text": "logistic-regression · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

chart.options.subtitle = {"text": "Exam Pass Probability vs Study Hours", "style": {"fontSize": "32px"}}

# X-axis
chart.options.x_axis = {
    "title": {"text": "Study Hours", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "min": 0,
    "max": 10,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Probability", "style": {"fontSize": "36px"}},
    "labels": {"style": {"fontSize": "28px"}},
    "min": -0.05,
    "max": 1.05,
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.1)",
    "plotLines": [
        {
            "value": 0.5,
            "color": "#888888",
            "width": 3,
            "dashStyle": "Dash",
            "label": {
                "text": "Decision Threshold (0.5)",
                "align": "right",
                "style": {"fontSize": "24px", "color": "#888888"},
                "x": -10,
                "y": -10,
            },
            "zIndex": 4,
        }
    ],
}

# Legend
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "28px"},
    "symbolRadius": 6,
    "symbolHeight": 20,
    "symbolWidth": 20,
}

# Plot options
chart.options.plot_options = {
    "scatter": {"marker": {"radius": 14, "symbol": "circle"}},
    "spline": {"lineWidth": 6, "marker": {"enabled": False}},
    "arearange": {"fillOpacity": 0.25, "lineWidth": 0, "marker": {"enabled": False}},
}

# Confidence interval (arearange series)
ci_data = [[float(x_curve[i]), float(ci_lower[i]), float(ci_upper[i])] for i in range(len(x_curve))]
ci_series = AreaRangeSeries()
ci_series.data = ci_data
ci_series.name = "95% CI"
ci_series.color = "rgba(48, 105, 152, 0.3)"
ci_series.fill_opacity = 0.3
chart.add_series(ci_series)

# Logistic curve
curve_data = [[float(x_curve[i]), float(y_prob[i])] for i in range(len(x_curve))]
curve_series = SplineSeries()
curve_series.data = curve_data
curve_series.name = "Logistic Curve"
curve_series.color = "#306998"
chart.add_series(curve_series)

# Class 0 points (Fail)
scatter_class0 = ScatterSeries()
scatter_class0.data = [[x_class0[i], y_class0[i]] for i in range(len(x_class0))]
scatter_class0.name = "Fail (0)"
scatter_class0.color = "rgba(48, 105, 152, 0.6)"
scatter_class0.marker = {"radius": 14, "symbol": "circle"}
chart.add_series(scatter_class0)

# Class 1 points (Pass)
scatter_class1 = ScatterSeries()
scatter_class1.data = [[x_class1[i], y_class1[i]] for i in range(len(x_class1))]
scatter_class1.name = "Pass (1)"
scatter_class1.color = "rgba(255, 212, 59, 0.8)"
scatter_class1.marker = {"radius": 14, "symbol": "circle"}
chart.add_series(scatter_class1)

# Add model accuracy annotation
accuracy = model.score(x.reshape(-1, 1), y)
chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": 8.5, "y": 0.15, "xAxis": 0, "yAxis": 0},
                "text": f"Accuracy: {accuracy:.1%}",
                "style": {"fontSize": "28px"},
                "backgroundColor": "rgba(255, 255, 255, 0.8)",
                "borderColor": "#306998",
                "borderWidth": 2,
                "padding": 15,
            }
        ],
        "labelOptions": {"shape": "rect"},
    }
]

# Credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download highcharts-more for arearange
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Download annotations module
annotations_url = "https://code.highcharts.com/modules/annotations.js"
with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
    <script>{annotations_js}</script>
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

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4900,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Save interactive HTML (using CDN scripts for standalone viewing)
html_export = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Logistic Regression - Highcharts</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_export)
