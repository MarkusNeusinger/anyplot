""" pyplots.ai
bar-stacked: Stacked Bar Chart
Library: highcharts unknown | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import ColumnSeries
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data: Monthly energy consumption by source (in MWh)
# Shows varied trajectories: Solar grows, Coal declines, Natural Gas fluctuates, Nuclear steady
categories = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
components = {
    "Solar": [120, 150, 210, 280, 350, 420],  # Strong growth (renewable adoption)
    "Natural Gas": [380, 320, 290, 340, 280, 310],  # Fluctuating (seasonal demand)
    "Nuclear": [450, 445, 455, 448, 452, 447],  # Steady baseline (consistent output)
    "Coal": [350, 310, 270, 220, 180, 140],  # Declining (phase-out)
}

# Colors: Python Blue, Python Yellow, then colorblind-safe additions
colors = ["#306998", "#FFD43B", "#9467BD", "#17BECF"]

# Create chart with container (CRITICAL for headless rendering)
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration with improved margins for Y-axis title
chart.options.chart = {
    "type": "column",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginBottom": 200,
    "marginTop": 120,
    "marginLeft": 200,  # More space for Y-axis title
    "spacingBottom": 50,
}

# Title
chart.options.title = {
    "text": "bar-stacked · highcharts · pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold"},
}

# Subtitle
chart.options.subtitle = {"text": "Monthly Energy Consumption by Source", "style": {"fontSize": "32px"}}

# X-axis (categories)
chart.options.x_axis = {
    "categories": categories,
    "title": {"text": "Month", "style": {"fontSize": "32px"}},
    "labels": {"style": {"fontSize": "28px"}},
}

# Y-axis with improved title spacing
chart.options.y_axis = {
    "title": {
        "text": "Energy (MWh)",
        "style": {"fontSize": "32px"},
        "margin": 30,  # More space between title and labels
    },
    "labels": {"style": {"fontSize": "28px"}},
    "gridLineWidth": 1,
    "gridLineColor": "#cccccc",
    "stackLabels": {"enabled": True, "style": {"fontSize": "24px", "fontWeight": "bold", "color": "#333333"}},
}

# Legend with larger text
chart.options.legend = {
    "enabled": True,
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal"},  # Increased from 28px
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "y": -30,
    "symbolRadius": 0,
    "symbolHeight": 24,
    "symbolWidth": 32,
}

# Plot options for stacking
chart.options.plot_options = {
    "column": {
        "stacking": "normal",
        "borderWidth": 2,
        "borderColor": "#ffffff",
        "dataLabels": {
            "enabled": True,
            "style": {"fontSize": "22px", "fontWeight": "normal", "color": "#333333"},
            "format": "{y}",
        },
    }
}

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "24px"},
    "headerFormat": "<b>{point.x}</b><br/>",
    "pointFormat": "{series.name}: {point.y} MWh<br/>Total: {point.stackTotal} MWh",
}

# Add series for each component
for i, (component_name, values) in enumerate(components.items()):
    series = ColumnSeries()
    series.name = component_name
    series.data = values
    series.color = colors[i % len(colors)]
    chart.add_series(series)

# Download Highcharts JS for inline embedding (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline script
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML file
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Create temp file for screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Screenshot using Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=5000,3000")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

# Screenshot the container element for exact 4800x2700 dimensions
container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

# Clean up temp file
Path(temp_path).unlink()
