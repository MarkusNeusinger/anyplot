""" pyplots.ai
confusion-matrix: Confusion Matrix Heatmap
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
from highcharts_core.options.series.heatmap import HeatmapSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Image Classification Model Results (4-class problem)
np.random.seed(42)
class_names = ["Cat", "Dog", "Bird", "Fish"]
n_classes = len(class_names)

# Realistic confusion matrix with varying accuracy per class
# Diagonal dominates (correct predictions), with realistic misclassification patterns
confusion_data = np.array(
    [
        [87, 8, 3, 2],  # Cat: often confused with Dog
        [12, 76, 7, 5],  # Dog: often confused with Cat
        [4, 6, 82, 8],  # Bird: sometimes confused with Fish
        [2, 4, 9, 85],  # Fish: sometimes confused with Bird
    ]
)

# Prepare data for heatmap format: [x_index, y_index, value]
heatmap_data = []
for i in range(n_classes):
    for j in range(n_classes):
        heatmap_data.append([j, n_classes - 1 - i, int(confusion_data[i, j])])

# Reversed class names for y-axis (to match matrix orientation)
reversed_classes = list(reversed(class_names))

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "heatmap",
    "width": 3600,
    "height": 3600,
    "backgroundColor": "#ffffff",
    "marginTop": 180,
    "marginBottom": 280,
    "marginLeft": 280,
    "marginRight": 220,
}

# Title
chart.options.title = {
    "text": "confusion-matrix · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Image Classification Model Performance",
    "style": {"fontSize": "32px", "color": "#666666"},
}

# X-axis - Predicted Labels
chart.options.x_axis = {
    "categories": class_names,
    "title": {"text": "Predicted Label", "style": {"fontSize": "36px", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "30px"}},
}

# Y-axis - True Labels
chart.options.y_axis = {
    "categories": reversed_classes,
    "title": {"text": "True Label", "style": {"fontSize": "36px", "fontWeight": "bold"}},
    "labels": {"style": {"fontSize": "30px"}},
    "reversed": False,
}

# Color axis - Sequential Blues colormap (colorblind-friendly)
chart.options.color_axis = {
    "min": 0,
    "max": 100,
    "stops": [
        [0, "#f7fbff"],  # Lightest blue
        [0.2, "#c6dbef"],
        [0.4, "#6baed6"],
        [0.6, "#2171b5"],
        [0.8, "#08519c"],
        [1.0, "#08306b"],  # Darkest blue
    ],
    "labels": {"style": {"fontSize": "24px"}, "format": "{value}"},
    "tickInterval": 20,
}

# Legend (colorbar)
chart.options.legend = {
    "align": "right",
    "layout": "vertical",
    "verticalAlign": "middle",
    "symbolHeight": 600,
    "itemStyle": {"fontSize": "24px"},
    "title": {"text": "Count", "style": {"fontSize": "28px"}},
}

# Tooltip
chart.options.tooltip = {
    "formatter": """function() {
        var predicted = this.series.xAxis.categories[this.point.x];
        var actual = this.series.yAxis.categories[this.point.y];
        var isCorrect = this.point.x === (3 - this.point.y);
        var label = isCorrect ? 'Correct' : 'Misclassified';
        return '<b>True: ' + actual + '</b><br>' +
               '<b>Predicted: ' + predicted + '</b><br>' +
               'Count: <b>' + this.point.value + '</b><br>' +
               '(' + label + ')';
    }""",
    "style": {"fontSize": "20px"},
}

# Disable credits
chart.options.credits = {"enabled": False}

# Create and add series
series = HeatmapSeries()
series.name = "Classification Results"
series.data = heatmap_data
series.border_width = 2
series.border_color = "#ffffff"
series.data_labels = {
    "enabled": True,
    "formatter": """function() {
        return this.point.value;
    }""",
    "style": {"fontSize": "40px", "fontWeight": "bold", "textOutline": "2px white", "color": "#000000"},
}

chart.add_series(series)

# Download Highcharts JS and Heatmap module
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

heatmap_url = "https://code.highcharts.com/modules/heatmap.js"
with urllib.request.urlopen(heatmap_url, timeout=30) as response:
    heatmap_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{heatmap_js}</script>
</head>
<body style="margin:0; background-color: #ffffff;">
    <div id="container" style="width: 3600px; height: 3600px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML file for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML file for interactive viewing
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Configure headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3600,3600")

# Take screenshot
driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
