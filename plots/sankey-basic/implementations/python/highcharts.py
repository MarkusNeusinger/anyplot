""" pyplots.ai
sankey-basic: Basic Sankey Diagram
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Reproducibility
np.random.seed(42)

# Data - Energy flow from sources to sectors (values in TWh - Terawatt-hours)
# Format: [source, target, value]
flows = [
    # Coal flows
    ["Coal", "Electricity", 150],
    ["Coal", "Industrial", 80],
    # Natural Gas flows
    ["Natural Gas", "Electricity", 120],
    ["Natural Gas", "Residential", 90],
    ["Natural Gas", "Commercial", 60],
    ["Natural Gas", "Industrial", 50],
    # Nuclear flows
    ["Nuclear", "Electricity", 200],
    # Petroleum flows
    ["Petroleum", "Transportation", 280],
    ["Petroleum", "Industrial", 70],
    ["Petroleum", "Residential", 30],
    # Renewable flows
    ["Renewable", "Electricity", 100],
    ["Renewable", "Transportation", 20],
    # Electricity flows to end uses
    ["Electricity", "Residential", 180],
    ["Electricity", "Commercial", 160],
    ["Electricity", "Industrial", 140],
]

# Collect unique nodes
nodes_set = set()
for source, target, _ in flows:
    nodes_set.add(source)
    nodes_set.add(target)
nodes = list(nodes_set)

# Colorblind-safe colors for nodes - all dark enough for white text contrast
node_colors = {
    # Sources (energy sources) - dark tones for white text readability
    "Coal": "#1A3A5C",  # Dark Blue
    "Natural Gas": "#6B4E12",  # Darker Goldenrod (darkened for contrast)
    "Nuclear": "#5B2E8F",  # Dark Purple
    "Petroleum": "#0A6B78",  # Dark Cyan
    "Renewable": "#155415",  # Dark Green
    # Intermediate - dark for contrast
    "Electricity": "#4D2A22",  # Dark Brown
    # End uses - darker shades for white text visibility
    "Residential": "#8B3A6B",  # Dark Rose
    "Commercial": "#3A3A3A",  # Darker Gray
    "Industrial": "#5B5C0A",  # Dark Olive
    "Transportation": "#994D00",  # Darker Orange
}

# Create nodes data with colors
nodes_data = [{"id": node, "name": node, "color": node_colors.get(node, "#306998")} for node in nodes]

# Create links data
links_data = [{"from": source, "to": target, "weight": value} for source, target, value in flows]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration with margins to prevent label cutoff at edges
chart.options.chart = {
    "type": "sankey",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 180,
    "marginRight": 180,
    "marginTop": 160,
    "marginBottom": 80,
}

# Title
chart.options.title = {
    "text": "sankey-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": "#333333"},
}

# Subtitle with units info
chart.options.subtitle = {"text": "U.S. Energy Flow (values in TWh)", "style": {"fontSize": "40px", "color": "#666666"}}

# Tooltip with units
chart.options.tooltip = {
    "style": {"fontSize": "36px"},
    "nodeFormat": "{point.name}: {point.sum} TWh",
    "pointFormat": "{point.fromNode.name} → {point.toNode.name}: {point.weight} TWh",
}

# Sankey series configuration
series_config = {
    "type": "sankey",
    "name": "Energy Flow",
    "keys": ["from", "to", "weight"],
    "nodes": nodes_data,
    "data": links_data,
    "dataLabels": {
        "enabled": True,
        "style": {"fontSize": "36px", "fontWeight": "bold", "color": "#FFFFFF", "textOutline": "3px #333333"},
        "nodeFormat": "{point.name}",
    },
    "nodeWidth": 50,
    "nodePadding": 35,
    "linkOpacity": 0.5,
    "curveFactor": 0.5,
    "colorByPoint": True,
    "linkColorMode": "from",
}

chart.options.series = [series_config]

# Disable legend for sankey (nodes are labeled)
chart.options.legend = {"enabled": False}

# Disable credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS and sankey module
highcharts_url = "https://code.highcharts.com/highcharts.js"
sankey_url = "https://code.highcharts.com/modules/sankey.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(sankey_url, timeout=30) as response:
    sankey_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{sankey_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version (use CDN for standalone) - fixed dimensions like PNG
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/sankey.js"></script>
</head>
<body style="margin:0; overflow:auto;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(standalone_html)

# Write temp HTML and take screenshot
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()  # Clean up temp file
