"""anyplot.ai
shap-summary: SHAP Summary Plot
Library: highcharts unknown | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-14
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - SHAP values for medical outcome prediction model
np.random.seed(42)
n_samples = 200
n_features = 12

feature_names = [
    "Blood Pressure (mmHg)",
    "Cholesterol (mg/dL)",
    "Glucose (mg/dL)",
    "BMI",
    "Heart Rate (bpm)",
    "Age (years)",
    "Hemoglobin A1C (%)",
    "Triglycerides (mg/dL)",
    "LDL Cholesterol (mg/dL)",
    "HDL Cholesterol (mg/dL)",
    "Smoking Status",
    "Physical Activity (min/week)",
]

# Generate feature values (normalized 0-1 for coloring)
feature_values = np.random.rand(n_samples, n_features)

# Generate SHAP values with varying importance per feature
# Features at top have higher magnitude SHAP values
importance_weights = np.linspace(1.5, 0.2, n_features)
shap_values = np.zeros((n_samples, n_features))

for i in range(n_features):
    # Create correlation between feature value and SHAP value
    base_effect = (feature_values[:, i] - 0.5) * importance_weights[i] * 2
    noise = np.random.randn(n_samples) * importance_weights[i] * 0.3
    shap_values[:, i] = base_effect + noise

# Sort features by mean absolute SHAP value (most important first)
feature_importance = np.mean(np.abs(shap_values), axis=0)
sorted_indices = np.argsort(feature_importance)[::-1]

# Take top 10 features
top_n = 10
sorted_indices = sorted_indices[:top_n]

# Prepare series data - one series per color bucket for gradient effect
# Use blue (low) to red (high) color gradient
n_color_bins = 10
color_gradient = [
    "#3B4CC0",  # Blue (low)
    "#5A7DC7",
    "#7AAAD0",
    "#A0C4DE",
    "#C5D5E8",
    "#E8C5C5",
    "#DEA0A0",
    "#D07A7A",
    "#C75A5A",
    "#C03B3B",  # Red (high)
]

all_series = []

for bin_idx in range(n_color_bins):
    bin_low = bin_idx / n_color_bins
    bin_high = (bin_idx + 1) / n_color_bins

    series_data = []

    for feat_idx, sorted_feat_idx in enumerate(sorted_indices):
        y_pos = top_n - 1 - feat_idx  # Invert so most important is at top

        for sample_idx in range(n_samples):
            feat_val = feature_values[sample_idx, sorted_feat_idx]

            if bin_low <= feat_val < bin_high or (bin_idx == n_color_bins - 1 and feat_val == 1.0):
                shap_val = shap_values[sample_idx, sorted_feat_idx]
                # Add jitter to reduce overlap
                jitter = np.random.uniform(-0.3, 0.3)
                series_data.append({"x": round(shap_val, 4), "y": y_pos + jitter})

    if series_data:
        series = ScatterSeries()
        series.data = series_data
        series.name = f"Feature Value: {bin_low:.1f}-{bin_high:.1f}"
        series.color = color_gradient[bin_idx]
        series.marker = {"radius": 8, "symbol": "circle"}
        series.show_in_legend = bin_idx in [0, 4, 9]  # Show only low, mid, high
        all_series.append(series)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": PAGE_BG,
    "marginLeft": 350,
    "marginBottom": 150,
}

# Title
chart.options.title = {
    "text": "shap-summary · highcharts · anyplot.ai",
    "style": {"fontSize": "32px", "fontWeight": "bold", "color": INK},
}

# X-axis (SHAP value)
chart.options.x_axis = {
    "title": {
        "text": "SHAP Value (Impact on Prediction)",
        "style": {"fontSize": "26px", "fontWeight": "600", "color": INK},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "22px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickColor": INK_SOFT,
    "tickLength": 8,
    "crosshair": {"color": INK_SOFT, "width": 2, "zIndex": 10},
    "plotLines": [{"value": 0, "color": INK_SOFT, "width": 4, "zIndex": 5, "dashStyle": "Solid"}],
}

# Y-axis (features)
y_categories = [feature_names[i] for i in sorted_indices][::-1]  # Reverse for top-to-bottom
chart.options.y_axis = {
    "title": {"text": "", "style": {"fontSize": "26px", "color": INK}},
    "categories": y_categories,
    "labels": {"style": {"fontSize": "24px", "color": INK_SOFT, "fontWeight": "500"}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "gridLineDashStyle": "Dot",
    "lineColor": INK_SOFT,
    "lineWidth": 2,
    "tickColor": INK_SOFT,
    "tickLength": 8,
    "reversed": False,
}

# Legend configuration for color scale
chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "middle",
    "layout": "vertical",
    "title": {"text": "Feature Value", "style": {"fontSize": "26px", "fontWeight": "bold", "color": INK}},
    "itemStyle": {"fontSize": "22px", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 2,
    "borderRadius": 4,
    "symbolRadius": 10,
    "symbolHeight": 24,
    "symbolWidth": 24,
    "itemMarginBottom": 12,
    "padding": 16,
}

# Plot options with enhanced Highcharts features
chart.options.plot_options = {
    "scatter": {
        "marker": {
            "radius": 8,
            "states": {
                "hover": {"enabled": True, "lineColor": INK, "lineWidth": 2, "radiusPlus": 3},
                "select": {"fillColor": INK_SOFT, "borderColor": INK},
            },
        },
        "jitter": {"x": 0, "y": 0},
        "cursor": "pointer",
    },
    "series": {"animation": False},
}

# Tooltip with enhanced styling
chart.options.tooltip = {
    "headerFormat": "<b>{series.name}</b><br>",
    "pointFormat": "SHAP Value: {point.x:.3f}",
    "style": {"fontSize": "20px", "color": INK},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 2,
    "borderRadius": 4,
    "padding": 12,
}

# Add all series
for s in all_series:
    chart.add_series(s)

# Download Highcharts JS
highcharts_url = "https://unpkg.com/highcharts@latest/highcharts.js"
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
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for PNG artifact
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
