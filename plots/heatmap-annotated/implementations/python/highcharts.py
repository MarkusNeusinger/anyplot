""" pyplots.ai
heatmap-annotated: Annotated Heatmap
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Correlation matrix for financial indicators
np.random.seed(42)
variables = ["Revenue", "Profit", "Growth", "ROI", "Debt", "Assets", "Employees"]
n = len(variables)

# Generate realistic correlation matrix (symmetric, diagonal = 1)
raw = np.random.randn(n, n) * 0.5
corr_matrix = (raw + raw.T) / 2
np.fill_diagonal(corr_matrix, 1.0)
corr_matrix = np.clip(corr_matrix, -1, 1)

# Prepare data for Highcharts heatmap format: [x_index, y_index, value]
data = []
for i in range(n):
    for j in range(n):
        data.append([j, i, round(corr_matrix[i, j], 2)])

# Build chart options as a dictionary for proper JSON serialization
chart_options = {
    "chart": {
        "type": "heatmap",
        "width": 3600,
        "height": 3600,
        "backgroundColor": "#ffffff",
        "marginTop": 150,
        "marginBottom": 200,
        "marginLeft": 250,
        "marginRight": 200,
    },
    "title": {
        "text": "heatmap-annotated · highcharts · pyplots.ai",
        "style": {"fontSize": "48px", "fontWeight": "bold"},
    },
    "xAxis": {
        "categories": variables,
        "title": {"text": "Variables", "style": {"fontSize": "36px"}},
        "labels": {"style": {"fontSize": "28px"}},
    },
    "yAxis": {
        "categories": variables,
        "title": {"text": "Variables", "style": {"fontSize": "36px"}},
        "labels": {"style": {"fontSize": "28px"}},
        "reversed": True,
    },
    "colorAxis": {
        "min": -1,
        "max": 1,
        "stops": [[0, "#306998"], [0.5, "#ffffff"], [1, "#FFD43B"]],
        "labels": {"style": {"fontSize": "24px"}},
    },
    "legend": {
        "align": "right",
        "layout": "vertical",
        "verticalAlign": "middle",
        "symbolHeight": 600,
        "itemStyle": {"fontSize": "24px"},
    },
    "credits": {"enabled": False},
    "series": [
        {
            "type": "heatmap",
            "name": "Correlation",
            "data": data,
            "borderWidth": 2,
            "borderColor": "#ffffff",
            "dataLabels": {
                "enabled": True,
                "format": "{point.value:.2f}",
                "style": {"fontSize": "26px", "fontWeight": "bold", "textOutline": "none"},
            },
        }
    ],
}

# Download Highcharts JS and heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
heatmap_url = "https://code.highcharts.com/modules/heatmap.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Convert options to JSON
options_json = json.dumps(chart_options)

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>
        Highcharts.chart('container', {options_json});
    </script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot using headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()
