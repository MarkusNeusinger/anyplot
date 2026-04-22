""" pyplots.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: highcharts unknown | Python 3.14.3
Quality: 93/100 | Created: 2026-02-17
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import LineSeries
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulate sensor data (12 features) and compute PCA via eigendecomposition
np.random.seed(42)
n_samples = 200
n_features = 12

# Create correlated features simulating industrial sensor readings
# A few latent factors drive most of the variance
latent = np.random.randn(n_samples, 3)
mixing = np.random.randn(3, n_features)
noise = np.random.randn(n_samples, n_features) * 0.5
X_raw = latent @ mixing + noise

# Standardize
X = (X_raw - X_raw.mean(axis=0)) / X_raw.std(axis=0)

# PCA via eigendecomposition of covariance matrix
cov_matrix = np.cov(X, rowvar=False)
eigenvalues, _ = np.linalg.eigh(cov_matrix)
eigenvalues = eigenvalues[::-1]  # Sort descending

explained_variance_ratio = eigenvalues / eigenvalues.sum()
n_components = list(range(1, n_features + 1))
individual_variance = explained_variance_ratio * 100
cumulative_variance = np.cumsum(individual_variance)

# Find threshold crossings
threshold_90 = next(i for i, v in enumerate(cumulative_variance) if v >= 90) + 1
threshold_95 = next(i for i, v in enumerate(cumulative_variance) if v >= 95) + 1

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafafa",
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
    "spacingBottom": 200,
    "spacingLeft": 80,
    "spacingTop": 60,
    "spacingRight": 80,
}

# Title
chart.options.title = {
    "text": "PCA Component Selection · line-pca-variance-cumulative · highcharts · pyplots.ai",
    "style": {"fontSize": "44px", "fontWeight": "600", "color": "#2c3e50"},
    "margin": 40,
}

# Subtitle
chart.options.subtitle = {
    "text": "Industrial Sensor Data (12 features) — explained variance by principal components",
    "style": {"fontSize": "30px", "color": "#7f8c8d", "fontWeight": "300"},
}

# X-axis
chart.options.x_axis = {
    "title": {
        "text": "Number of Components",
        "style": {"fontSize": "34px", "color": "#34495e", "fontWeight": "500"},
        "margin": 25,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#555555"}},
    "categories": [str(n) for n in n_components],
    "tickInterval": 1,
    "lineColor": "#bdc3c7",
    "lineWidth": 2,
    "tickColor": "#bdc3c7",
    "tickWidth": 1,
    "tickLength": 8,
}

# Y-axis
chart.options.y_axis = {
    "title": {
        "text": "Explained Variance (%)",
        "style": {"fontSize": "34px", "color": "#34495e", "fontWeight": "500"},
        "margin": 30,
    },
    "labels": {"style": {"fontSize": "28px", "color": "#555555"}, "format": "{value}%"},
    "min": 0,
    "max": 100,
    "endOnTick": False,
    "tickInterval": 10,
    "gridLineWidth": 1,
    "gridLineColor": "#ecf0f1",
    "gridLineDashStyle": "Dot",
    "lineColor": "#bdc3c7",
    "lineWidth": 2,
    "plotLines": [
        {
            "value": 90,
            "color": "#E67E22",
            "width": 3,
            "dashStyle": "LongDash",
            "label": {
                "text": "90%",
                "align": "left",
                "style": {"fontSize": "24px", "color": "#E67E22", "fontWeight": "600"},
                "x": 10,
                "y": -10,
            },
            "zIndex": 4,
        },
        {
            "value": 95,
            "color": "#8E44AD",
            "width": 3,
            "dashStyle": "LongDash",
            "label": {
                "text": "95%",
                "align": "left",
                "style": {"fontSize": "24px", "color": "#8E44AD", "fontWeight": "600"},
                "x": 10,
                "y": -10,
            },
            "zIndex": 4,
        },
    ],
}

# Legend - floating inside plot area in empty lower-right region
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "26px", "fontWeight": "400", "color": "#34495e"},
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "floating": True,
    "backgroundColor": "rgba(255,255,255,0.9)",
    "borderRadius": 8,
    "borderWidth": 1,
    "borderColor": "#ecf0f1",
    "symbolWidth": 36,
    "symbolHeight": 16,
    "itemMarginBottom": 10,
    "padding": 20,
    "x": -50,
    "y": 200,
}

# Plot options
chart.options.plot_options = {
    "series": {"animation": False},
    "line": {
        "lineWidth": 5,
        "marker": {"enabled": True, "radius": 10, "symbol": "circle"},
        "shadow": {"color": "rgba(0,0,0,0.08)", "offsetX": 1, "offsetY": 2, "width": 4},
    },
    "column": {"borderWidth": 0, "borderRadius": 4, "pointPadding": 0.12, "groupPadding": 0.08},
}

# Tooltip
chart.options.tooltip = {
    "shared": True,
    "style": {"fontSize": "24px"},
    "headerFormat": "<b>Component {point.key}</b><br/>",
    "pointFormat": "{series.name}: <b>{point.y:.1f}%</b><br/>",
}

# Individual variance as column series (subtle background)
col_series = ColumnSeries()
col_series.name = "Individual Variance"
col_series.data = [round(float(v), 2) for v in individual_variance]
col_series.color = "rgba(48, 105, 152, 0.25)"
chart.add_series(col_series)

# Cumulative variance as line series (main focus)
line_series = LineSeries()
line_series.name = "Cumulative Variance"
line_series.data = [round(float(v), 2) for v in cumulative_variance]
line_series.color = "#306998"
line_series.marker = {"fillColor": "#306998", "lineWidth": 2, "lineColor": "#ffffff"}
chart.add_series(line_series)

# Mark 90% threshold point
val_90 = round(float(cumulative_variance[threshold_90 - 1]), 1)
marker_90 = ScatterSeries()
marker_90.name = f"90% at {threshold_90} components"
marker_90.data = [[threshold_90 - 1, round(float(cumulative_variance[threshold_90 - 1]), 2)]]
marker_90.color = "#E67E22"
marker_90.marker = {"radius": 16, "symbol": "diamond", "fillColor": "#E67E22", "lineWidth": 3, "lineColor": "#ffffff"}
chart.add_series(marker_90)

# Mark 95% threshold point
val_95 = round(float(cumulative_variance[threshold_95 - 1]), 1)
marker_95 = ScatterSeries()
marker_95.name = f"95% at {threshold_95} components"
marker_95.data = [[threshold_95 - 1, round(float(cumulative_variance[threshold_95 - 1]), 2)]]
marker_95.color = "#8E44AD"
marker_95.marker = {"radius": 16, "symbol": "diamond", "fillColor": "#8E44AD", "lineWidth": 3, "lineColor": "#ffffff"}
chart.add_series(marker_95)

# Annotations for data storytelling — insight callouts at threshold crossings
chart.options.annotations = [
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": "rgba(255,255,255,0.92)",
            "borderColor": "#E67E22",
            "borderWidth": 2,
            "borderRadius": 8,
            "padding": 18,
            "style": {"fontSize": "26px", "color": "#2c3e50", "fontWeight": "500"},
            "shape": "callout",
            "verticalAlign": "top",
        },
        "labels": [
            {
                "point": {"x": threshold_90 - 1, "y": val_90, "xAxis": 0, "yAxis": 0},
                "text": f"Only {threshold_90} components explain {val_90}% of variance",
                "y": 60,
                "x": 80,
            }
        ],
    },
    {
        "draggable": "",
        "labelOptions": {
            "backgroundColor": "rgba(255,255,255,0.92)",
            "borderColor": "#8E44AD",
            "borderWidth": 2,
            "borderRadius": 8,
            "padding": 18,
            "style": {"fontSize": "26px", "color": "#2c3e50", "fontWeight": "500"},
            "shape": "callout",
            "verticalAlign": "top",
        },
        "labels": [
            {
                "point": {"x": threshold_95 - 1, "y": val_95, "xAxis": 0, "yAxis": 0},
                "text": f"{threshold_95} components reach {val_95}% — diminishing returns beyond",
                "y": 60,
                "x": 100,
            }
        ],
    },
]

# Download Highcharts JS and annotations module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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

# Save interactive HTML
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
