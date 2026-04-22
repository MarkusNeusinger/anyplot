""" pyplots.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
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
from highcharts_core.options.series.scatter import ScatterSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulated word embeddings after dimensionality reduction
np.random.seed(42)

# Create clusters of related words in 2D space
programming_words = ["Python", "JavaScript", "Java", "C++", "Ruby", "Rust", "Go", "Swift"]
data_words = ["Pandas", "NumPy", "TensorFlow", "PyTorch", "Scikit-learn", "Keras"]
web_words = ["React", "Vue", "Angular", "Django", "Flask", "Node.js"]
database_words = ["PostgreSQL", "MongoDB", "Redis", "MySQL", "SQLite", "Cassandra"]

# Create clustered positions - more compact to avoid clipping
x_coords = []
y_coords = []

# Programming languages cluster (center-left)
for _ in programming_words:
    x_coords.append(np.random.normal(-2.5, 0.7))
    y_coords.append(np.random.normal(2, 0.7))

# Data science tools cluster (top-right)
for _ in data_words:
    x_coords.append(np.random.normal(2.5, 0.6))
    y_coords.append(np.random.normal(2.5, 0.6))

# Web frameworks cluster (bottom-right)
for _ in web_words:
    x_coords.append(np.random.normal(2, 0.5))
    y_coords.append(np.random.normal(-2, 0.5))

# Databases cluster (bottom-left)
for _ in database_words:
    x_coords.append(np.random.normal(-2, 0.6))
    y_coords.append(np.random.normal(-2, 0.6))

x = np.array(x_coords)
y = np.array(y_coords)

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Create chart with container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration with margins to prevent clipping
chart.options.chart = {
    "type": "scatter",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 250,
    "marginRight": 300,
    "marginTop": 200,
    "marginBottom": 300,
}

# Title - large font for 4800px canvas
chart.options.title = {
    "text": "scatter-text · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold", "color": "#333333"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Tech Stack Word Embeddings (2D Projection)",
    "style": {"fontSize": "48px", "color": "#666666"},
}

# Axes - scaled for large canvas
chart.options.x_axis = {
    "title": {"text": "Dimension 1", "style": {"fontSize": "48px", "color": "#333333"}},
    "labels": {"style": {"fontSize": "36px", "color": "#333333"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.15)",
    "lineWidth": 2,
    "lineColor": "#333333",
    "tickWidth": 2,
    "tickLength": 15,
}

chart.options.y_axis = {
    "title": {"text": "Dimension 2", "style": {"fontSize": "48px", "color": "#333333"}},
    "labels": {"style": {"fontSize": "36px", "color": "#333333"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0,0,0,0.15)",
    "lineWidth": 2,
    "lineColor": "#333333",
    "tickWidth": 2,
    "tickLength": 15,
}

# Legend - show categories at top right to not interfere with data
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal"},
    "layout": "vertical",
    "align": "right",
    "verticalAlign": "top",
    "x": -50,
    "y": 100,
    "borderWidth": 1,
    "borderColor": "#cccccc",
    "backgroundColor": "#ffffff",
    "padding": 20,
}

# Create data points with text labels using dataLabels
# Group by category for different colors
categories = {
    "Programming Languages": (programming_words, "#306998", 0),
    "Data Science": (data_words, "#FFD43B", len(programming_words)),
    "Web Frameworks": (web_words, "#9467BD", len(programming_words) + len(data_words)),
    "Databases": (database_words, "#17BECF", len(programming_words) + len(data_words) + len(web_words)),
}

# Add series for each category
for cat_name, (words, color, start_idx) in categories.items():
    series = ScatterSeries()
    series.name = cat_name

    # Create data points with labels - large fonts for 4800px canvas
    data_points = []
    for i, word in enumerate(words):
        idx = start_idx + i
        data_points.append(
            {
                "x": float(x[idx]),
                "y": float(y[idx]),
                "name": word,
                "dataLabels": {
                    "enabled": True,
                    "format": word,
                    "style": {"fontSize": "42px", "fontWeight": "bold", "color": color, "textOutline": "3px white"},
                    "allowOverlap": True,
                },
            }
        )

    series.data = data_points

    # Hide markers - text labels are the visual elements
    series.marker = {"enabled": False}

    series.color = color

    chart.add_series(series)

# Plot options for data labels
chart.options.plot_options = {
    "scatter": {"marker": {"enabled": False}, "dataLabels": {"enabled": True, "style": {"fontSize": "42px"}}}
}

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and capture screenshot
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

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    # Use CDN for HTML file (works in browsers)
    html_interactive = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(html_interactive)
