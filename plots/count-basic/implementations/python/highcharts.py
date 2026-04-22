""" pyplots.ai
count-basic: Basic Count Plot
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-25
"""

import tempfile
import time
import urllib.request
from collections import Counter
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Survey responses (raw categorical data to be counted)
responses = [
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Satisfied",
    "Very Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Neutral",
    "Very Satisfied",
    "Satisfied",
    "Very Dissatisfied",
    "Satisfied",
    "Dissatisfied",
    "Neutral",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
    "Neutral",
    "Very Satisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Neutral",
    "Satisfied",
    "Dissatisfied",
    "Satisfied",
    "Satisfied",
    "Very Satisfied",
    "Satisfied",
]

# Count occurrences
counts = Counter(responses)

# Sort by frequency (descending)
sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
categories = [item[0] for item in sorted_counts]
values = [item[1] for item in sorted_counts]

# Create chart with container specified (CRITICAL for PNG export)
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration for 4800x2700 px
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 280,
    "marginTop": 120,
}

# Title
chart.options.title = {
    "text": "count-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "72px", "fontWeight": "bold"},
}

# X-axis with categories
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Response Category", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
}

# Y-axis
chart.options.y_axis = {
    "title": {"text": "Count", "style": {"fontSize": "48px"}},
    "labels": {"style": {"fontSize": "36px"}},
    "gridLineColor": "#e0e0e0",
    "gridLineWidth": 1,
}

# Legend disabled (single series)
chart.options.legend = {"enabled": False}

# Plot options with data labels
chart.options.plot_options = {
    "column": {
        "dataLabels": {"enabled": True, "format": "{y}", "style": {"fontSize": "32px", "fontWeight": "bold"}},
        "borderRadius": 4,
        "borderWidth": 0,
    }
}

# Create series with Python Blue color
series = ColumnSeries()
series.data = values
series.name = "Count"
series.color = "#306998"

chart.add_series(series)

# Download Highcharts JS for inline embedding
highcharts_url = "https://code.highcharts.com/highcharts.js"
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
<body style="margin:0; padding:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Also save the HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Selenium headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
