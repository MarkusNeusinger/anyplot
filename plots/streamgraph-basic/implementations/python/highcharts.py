""" pyplots.ai
streamgraph-basic: Basic Stream Graph
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.area import StreamGraphSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Monthly streaming hours by music genre over two years
np.random.seed(42)
months = np.arange(24)  # 24 months
month_labels = [
    "Jan '23",
    "Feb '23",
    "Mar '23",
    "Apr '23",
    "May '23",
    "Jun '23",
    "Jul '23",
    "Aug '23",
    "Sep '23",
    "Oct '23",
    "Nov '23",
    "Dec '23",
    "Jan '24",
    "Feb '24",
    "Mar '24",
    "Apr '24",
    "May '24",
    "Jun '24",
    "Jul '24",
    "Aug '24",
    "Sep '24",
    "Oct '24",
    "Nov '24",
    "Dec '24",
]

# Generate genre data with realistic patterns
genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz"]
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF", "#E377C2"]

# Base values and trends for each genre
genre_data = {}
genre_data["Pop"] = 4000 + 200 * np.sin(2 * np.pi * months / 12) + np.random.normal(0, 200, 24)
genre_data["Rock"] = 2500 - months * 30 + 150 * np.sin(2 * np.pi * months / 6) + np.random.normal(0, 150, 24)
genre_data["Hip-Hop"] = 2000 + months * 80 + 100 * np.sin(2 * np.pi * months / 4) + np.random.normal(0, 180, 24)
genre_data["Electronic"] = 1800 + 300 * np.sin(2 * np.pi * months / 12 + np.pi) + np.random.normal(0, 120, 24)
genre_data["Jazz"] = 1200 + 50 * np.sin(2 * np.pi * months / 8) + np.random.normal(0, 80, 24)

# Ensure no negative values
for genre in genres:
    genre_data[genre] = np.clip(genre_data[genre], 300, None)

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "streamgraph",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 250,
    "marginLeft": 200,
    "marginRight": 100,
}

# Title
chart.options.title = {
    "text": "Music Streaming Trends · streamgraph-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Monthly streaming hours by genre (2023-2024)", "style": {"fontSize": "36px"}}

# X-axis with category labels
chart.options.x_axis = {"categories": month_labels, "labels": {"style": {"fontSize": "28px"}}, "crosshair": True}

# Y-axis (hidden for streamgraph as values are relative)
chart.options.y_axis = {"visible": False, "startOnTick": False, "endOnTick": False}

# Plot options for streamgraph styling
chart.options.plot_options = {"streamgraph": {"fillOpacity": 0.85, "lineWidth": 0, "marker": {"enabled": False}}}

# Legend configuration
chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "itemStyle": {"fontSize": "32px"},
    "symbolWidth": 40,
    "symbolHeight": 20,
    "symbolRadius": 6,
    "y": 20,
}

# Colors
chart.options.colors = colors

# Add series for each genre
for genre in genres:
    series = StreamGraphSeries()
    series.data = [float(v) for v in genre_data[genre]]
    series.name = genre
    chart.add_series(series)

# Download Highcharts JS and streamgraph module for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

streamgraph_url = "https://code.highcharts.com/modules/streamgraph.js"
with urllib.request.urlopen(streamgraph_url, timeout=30) as response:
    streamgraph_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{streamgraph_js}</script>
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

# Also save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/streamgraph.js"></script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>"""
    f.write(standalone_html)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render

# Screenshot the chart element specifically for exact 4800x2700
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
