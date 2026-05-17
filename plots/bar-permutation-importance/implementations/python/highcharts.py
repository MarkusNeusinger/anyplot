"""anyplot.ai
bar-permutation-importance: Permutation Feature Importance Plot
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-05-17
"""

import json
import os
import tempfile
import time
from pathlib import Path

import numpy as np
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme-adaptive tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - Simulating permutation importance from a medical diagnosis model (diabetes prediction)
np.random.seed(42)

features = [
    "HbA1c Level",
    "Fasting Glucose",
    "BMI",
    "Blood Pressure Systolic",
    "Age",
    "Cholesterol",
    "Triglycerides",
    "Family History Score",
    "Physical Activity",
    "Sleep Duration",
    "Medication Count",
    "Waist Circumference",
]

# Generate realistic importance values (decreasing model score)
base_importance = np.array([0.42, 0.38, 0.32, 0.25, 0.18, 0.14, 0.10, 0.08, 0.06, 0.03, 0.01, -0.02])
importance_mean = base_importance + np.random.uniform(-0.03, 0.03, len(features))
importance_std = np.abs(importance_mean) * np.random.uniform(0.25, 0.55, len(features))

# Sort by importance (highest first)
sorted_indices = np.argsort(importance_mean)[::-1]
features = [features[i] for i in sorted_indices]
importance_mean = importance_mean[sorted_indices]
importance_std = importance_std[sorted_indices]

# Create sequential color gradient based on importance (viridis-inspired)
# Map importance to a color from light yellow-green to dark green
max_imp = float(np.max(importance_mean))
min_imp = float(np.min(importance_mean))

# Use a viridis-like sequential gradient
colors = [
    "#FDE725",
    "#ADDC30",
    "#5EC962",
    "#31688E",
    "#440154",
    "#31688E",
    "#31688E",
    "#31688E",
    "#440154",
    "#440154",
    "#440154",
    "#440154",
]

# Map each importance value to a position in the gradient
bar_data = []
for imp in importance_mean:
    if max_imp == min_imp:
        color_idx = len(colors) // 2
    else:
        # Normalize importance to [0, 1]
        normalized = (imp - min_imp) / (max_imp - min_imp)
        color_idx = min(int(normalized * len(colors)), len(colors) - 1)
    bar_data.append({"y": float(imp), "color": colors[color_idx]})

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
        "backgroundColor": PAGE_BG,
        "marginLeft": 400,
        "marginRight": 100,
        "marginBottom": 200,
        "marginTop": 180,
    },
    "title": {
        "text": "bar-permutation-importance · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "fontWeight": "medium", "color": INK},
    },
    "subtitle": {
        "text": "Diabetes Prediction Model - Permutation Importance (n_repeats=10)",
        "style": {"fontSize": "20px", "color": INK_SOFT},
    },
    "xAxis": {
        "categories": features,
        "title": None,
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
        "gridLineColor": GRID,
    },
    "yAxis": {
        "title": {"text": "Mean Decrease in AUC Score", "style": {"fontSize": "22px", "color": INK}},
        "labels": {"style": {"fontSize": "18px", "color": INK_SOFT}},
        "plotLines": [{"value": 0, "color": INK_SOFT, "width": 2, "zIndex": 5}],
        "gridLineWidth": 1,
        "gridLineColor": GRID,
        "lineColor": INK_SOFT,
        "tickColor": INK_SOFT,
    },
    "tooltip": {
        "headerFormat": '<span style="font-size: 18px; font-weight: bold; color: {INK};">{point.key}</span><br/>',
        "pointFormat": '<span style="font-size: 16px; color: {INK};">Importance: <b>{point.y:.4f}</b></span>',
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
    },
    "legend": {
        "enabled": True,
        "itemStyle": {"color": INK_SOFT, "fontSize": "16px"},
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
    },
    "credits": {"enabled": False},
    "plotOptions": {
        "bar": {"pointPadding": 0.05, "groupPadding": 0.05, "borderWidth": 0},
        "errorbar": {"stemWidth": 6, "whiskerLength": "50%", "whiskerWidth": 6, "color": INK_SOFT},
    },
    "series": [
        {"name": "Importance (Color = Relative Magnitude)", "data": bar_data, "type": "bar"},
        {"name": "Variability (±1 Std Dev)", "data": error_data, "type": "errorbar", "linkedTo": ":previous"},
    ],
}

# Download Highcharts JS with retry logic
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/javascript, application/javascript",
    "Referer": "https://code.highcharts.com/",
}

for attempt in range(3):
    try:
        resp = requests.get("https://code.highcharts.com/highcharts.js", headers=headers, timeout=30)
        resp.raise_for_status()
        highcharts_js = resp.text
        break
    except Exception:
        if attempt == 2:
            raise
        time.sleep(2)

for attempt in range(3):
    try:
        resp = requests.get("https://code.highcharts.com/highcharts-more.js", headers=headers, timeout=30)
        resp.raise_for_status()
        highcharts_more_js = resp.text
        break
    except Exception:
        if attempt == 2:
            raise
        time.sleep(2)

# Generate HTML with inline scripts
chart_options_json = json.dumps(chart_options)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {chart_options_json});
    </script>
</body>
</html>"""

# Write temp HTML and take screenshot for PNG
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

# Save HTML for interactive version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)
