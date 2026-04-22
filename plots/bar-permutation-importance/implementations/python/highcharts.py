""" pyplots.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulating permutation importance from a house price prediction model
np.random.seed(42)

features = [
    "Square Footage",
    "Number of Bedrooms",
    "Location Score",
    "Year Built",
    "Lot Size",
    "Garage Spaces",
    "Number of Bathrooms",
    "School Rating",
    "Distance to Center",
    "Property Tax Rate",
    "Crime Index",
    "Median Income",
    "Walk Score",
    "Transit Score",
    "Renovation Year",
]

# Generate realistic importance values (decreasing model score)
base_importance = np.array([0.35, 0.28, 0.22, 0.18, 0.15, 0.12, 0.10, 0.08, 0.06, 0.04, 0.03, 0.02, 0.01, 0.005, -0.01])
importance_mean = base_importance + np.random.uniform(-0.02, 0.02, len(features))
importance_std = np.abs(importance_mean) * np.random.uniform(0.2, 0.5, len(features))

# Sort by importance (highest first)
sorted_indices = np.argsort(importance_mean)[::-1]
features = [features[i] for i in sorted_indices]
importance_mean = importance_mean[sorted_indices]
importance_std = importance_std[sorted_indices]

# Create color gradient based on importance (blue gradient with more contrast)
max_imp = float(max(importance_mean))
min_imp = float(min(importance_mean))


def get_color(value):
    """Map value to color gradient from light blue to Python Blue."""
    if max_imp == min_imp:
        t = 0.5
    else:
        t = (value - min_imp) / (max_imp - min_imp)
    # Gradient from very light (#B8D4E8) to Python Blue (#306998)
    r = int(184 + (48 - 184) * t)
    g = int(212 + (105 - 212) * t)
    b = int(232 + (152 - 232) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# Prepare data for bars with individual colors
bar_data = []
for imp in importance_mean:
    bar_data.append({"y": float(imp), "color": get_color(float(imp))})

# Prepare error bar data
error_data = []
for imp, std in zip(importance_mean, importance_std, strict=True):
    error_data.append([float(imp - std), float(imp + std)])

# Build Highcharts options as dict
chart_options = {
    "chart": {
        "type": "bar",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginLeft": 400,
        "marginRight": 100,
        "marginBottom": 200,
        "marginTop": 180,
    },
    "title": {
        "text": "bar-permutation-importance · highcharts · pyplots.ai",
        "style": {"fontSize": "56px", "fontWeight": "bold"},
    },
    "subtitle": {
        "text": "House Price Prediction Model - Permutation Importance (n_repeats=10)",
        "style": {"fontSize": "38px", "color": "#666666"},
    },
    "xAxis": {"categories": features, "title": None, "labels": {"style": {"fontSize": "34px"}}},
    "yAxis": {
        "title": {"text": "Mean Decrease in R² Score", "style": {"fontSize": "40px"}},
        "labels": {"style": {"fontSize": "28px"}},
        "plotLines": [{"value": 0, "color": "#333333", "width": 4, "zIndex": 5}],
        "gridLineWidth": 1,
        "gridLineColor": "#E5E5E5",
    },
    "tooltip": {
        "headerFormat": '<span style="font-size: 30px; font-weight: bold;">{point.key}</span><br/>',
        "pointFormat": '<span style="font-size: 28px">Importance: <b>{point.y:.4f}</b></span>',
    },
    "legend": {"enabled": False},
    "credits": {"enabled": False},
    "plotOptions": {
        "bar": {"pointPadding": 0.05, "groupPadding": 0.05, "borderWidth": 2, "borderColor": "#1a3a5c"},
        "errorbar": {"stemWidth": 6, "whiskerLength": "50%", "whiskerWidth": 6, "color": "#1a3a5c"},
    },
    "series": [
        {"name": "Importance", "data": bar_data, "type": "bar"},
        {"name": "Error", "data": error_data, "type": "errorbar", "linkedTo": ":previous"},
    ],
}

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Download highcharts-more for error bars
highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
    highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {chart_options_json});
    </script>
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
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

# Also save HTML for interactive version
html_interactive = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>bar-permutation-importance · highcharts · pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>
        Highcharts.chart('container', {chart_options_json});
    </script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_interactive)
