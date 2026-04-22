""" pyplots.ai
parallel-categories-basic: Basic Parallel Categories Plot
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-30
"""

import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Titanic passenger survival data
# Format: [from_node, to_node, count]
# Columns: Class -> Sex -> Age Group -> Survival

flows = [
    # First Class flows
    ["1st Class", "Male_1st", 180],
    ["1st Class", "Female_1st", 145],
    ["Male_1st", "Adult_M1", 175],
    ["Male_1st", "Child_M1", 5],
    ["Female_1st", "Adult_F1", 140],
    ["Female_1st", "Child_F1", 5],
    ["Adult_M1", "Survived_AM1", 57],
    ["Adult_M1", "Died_AM1", 118],
    ["Child_M1", "Survived_CM1", 5],
    ["Child_M1", "Died_CM1", 0],
    ["Adult_F1", "Survived_AF1", 135],
    ["Adult_F1", "Died_AF1", 5],
    ["Child_F1", "Survived_CF1", 5],
    ["Child_F1", "Died_CF1", 0],
    # Second Class flows
    ["2nd Class", "Male_2nd", 179],
    ["2nd Class", "Female_2nd", 106],
    ["Male_2nd", "Adult_M2", 168],
    ["Male_2nd", "Child_M2", 11],
    ["Female_2nd", "Adult_F2", 93],
    ["Female_2nd", "Child_F2", 13],
    ["Adult_M2", "Survived_AM2", 15],
    ["Adult_M2", "Died_AM2", 153],
    ["Child_M2", "Survived_CM2", 11],
    ["Child_M2", "Died_CM2", 0],
    ["Adult_F2", "Survived_AF2", 80],
    ["Adult_F2", "Died_AF2", 13],
    ["Child_F2", "Survived_CF2", 13],
    ["Child_F2", "Died_CF2", 0],
    # Third Class flows
    ["3rd Class", "Male_3rd", 510],
    ["3rd Class", "Female_3rd", 196],
    ["Male_3rd", "Adult_M3", 478],
    ["Male_3rd", "Child_M3", 32],
    ["Female_3rd", "Adult_F3", 152],
    ["Female_3rd", "Child_F3", 44],
    ["Adult_M3", "Survived_AM3", 75],
    ["Adult_M3", "Died_AM3", 403],
    ["Child_M3", "Survived_CM3", 13],
    ["Child_M3", "Died_CM3", 19],
    ["Adult_F3", "Survived_AF3", 76],
    ["Adult_F3", "Died_AF3", 76],
    ["Child_F3", "Survived_CF3", 14],
    ["Child_F3", "Died_CF3", 30],
]

# Filter out zero flows
flows = [f for f in flows if f[2] > 0]

# Colorblind-safe colors for categories
colors = {
    # Class colors
    "1st Class": "#306998",  # Python Blue
    "2nd Class": "#9467BD",  # Purple
    "3rd Class": "#17BECF",  # Cyan
    # Sex colors
    "Male_1st": "#2E5A7E",
    "Male_2nd": "#2E5A7E",
    "Male_3rd": "#2E5A7E",
    "Female_1st": "#E377C2",
    "Female_2nd": "#E377C2",
    "Female_3rd": "#E377C2",
    # Age colors
    "Adult_M1": "#5B4B8A",
    "Adult_M2": "#5B4B8A",
    "Adult_M3": "#5B4B8A",
    "Adult_F1": "#5B4B8A",
    "Adult_F2": "#5B4B8A",
    "Adult_F3": "#5B4B8A",
    "Child_M1": "#8FBC8F",
    "Child_M2": "#8FBC8F",
    "Child_M3": "#8FBC8F",
    "Child_F1": "#8FBC8F",
    "Child_F2": "#8FBC8F",
    "Child_F3": "#8FBC8F",
    # Survival colors
    "Survived_AM1": "#2E7D32",
    "Survived_CM1": "#2E7D32",
    "Survived_AF1": "#2E7D32",
    "Survived_CF1": "#2E7D32",
    "Survived_AM2": "#2E7D32",
    "Survived_CM2": "#2E7D32",
    "Survived_AF2": "#2E7D32",
    "Survived_CF2": "#2E7D32",
    "Survived_AM3": "#2E7D32",
    "Survived_CM3": "#2E7D32",
    "Survived_AF3": "#2E7D32",
    "Survived_CF3": "#2E7D32",
    "Died_AM1": "#C62828",
    "Died_CM1": "#C62828",
    "Died_AF1": "#C62828",
    "Died_CF1": "#C62828",
    "Died_AM2": "#C62828",
    "Died_CM2": "#C62828",
    "Died_AF2": "#C62828",
    "Died_CF2": "#C62828",
    "Died_AM3": "#C62828",
    "Died_CM3": "#C62828",
    "Died_AF3": "#C62828",
    "Died_CF3": "#C62828",
}

# Display names for nodes
display_names = {
    "1st Class": "1st Class",
    "2nd Class": "2nd Class",
    "3rd Class": "3rd Class",
    "Male_1st": "Male",
    "Male_2nd": "Male",
    "Male_3rd": "Male",
    "Female_1st": "Female",
    "Female_2nd": "Female",
    "Female_3rd": "Female",
    "Adult_M1": "Adult",
    "Adult_M2": "Adult",
    "Adult_M3": "Adult",
    "Adult_F1": "Adult",
    "Adult_F2": "Adult",
    "Adult_F3": "Adult",
    "Child_M1": "Child",
    "Child_M2": "Child",
    "Child_M3": "Child",
    "Child_F1": "Child",
    "Child_F2": "Child",
    "Child_F3": "Child",
    "Survived_AM1": "Survived",
    "Survived_CM1": "Survived",
    "Survived_AF1": "Survived",
    "Survived_CF1": "Survived",
    "Survived_AM2": "Survived",
    "Survived_CM2": "Survived",
    "Survived_AF2": "Survived",
    "Survived_CF2": "Survived",
    "Survived_AM3": "Survived",
    "Survived_CM3": "Survived",
    "Survived_AF3": "Survived",
    "Survived_CF3": "Survived",
    "Died_AM1": "Died",
    "Died_CM1": "Died",
    "Died_AF1": "Died",
    "Died_CF1": "Died",
    "Died_AM2": "Died",
    "Died_CM2": "Died",
    "Died_AF2": "Died",
    "Died_CF2": "Died",
    "Died_AM3": "Died",
    "Died_CM3": "Died",
    "Died_AF3": "Died",
    "Died_CF3": "Died",
}

# Column positions for parallel categories structure
column_map = {
    "1st Class": 0,
    "2nd Class": 0,
    "3rd Class": 0,
    "Male_1st": 1,
    "Male_2nd": 1,
    "Male_3rd": 1,
    "Female_1st": 1,
    "Female_2nd": 1,
    "Female_3rd": 1,
    "Adult_M1": 2,
    "Adult_M2": 2,
    "Adult_M3": 2,
    "Adult_F1": 2,
    "Adult_F2": 2,
    "Adult_F3": 2,
    "Child_M1": 2,
    "Child_M2": 2,
    "Child_M3": 2,
    "Child_F1": 2,
    "Child_F2": 2,
    "Child_F3": 2,
    "Survived_AM1": 3,
    "Survived_CM1": 3,
    "Survived_AF1": 3,
    "Survived_CF1": 3,
    "Survived_AM2": 3,
    "Survived_CM2": 3,
    "Survived_AF2": 3,
    "Survived_CF2": 3,
    "Survived_AM3": 3,
    "Survived_CM3": 3,
    "Survived_AF3": 3,
    "Survived_CF3": 3,
    "Died_AM1": 3,
    "Died_CM1": 3,
    "Died_AF1": 3,
    "Died_CF1": 3,
    "Died_AM2": 3,
    "Died_CM2": 3,
    "Died_AF2": 3,
    "Died_CF2": 3,
    "Died_AM3": 3,
    "Died_CM3": 3,
    "Died_AF3": 3,
    "Died_CF3": 3,
}

# Collect unique nodes from flows
nodes_set = set()
for source, target, _ in flows:
    nodes_set.add(source)
    nodes_set.add(target)

# Create nodes data with column positions and colors
nodes_data = [
    {
        "id": node,
        "name": display_names.get(node, node),
        "column": column_map.get(node, 0),
        "color": colors.get(node, "#306998"),
    }
    for node in nodes_set
]

# Create links data
links_data = [{"from": source, "to": target, "weight": value} for source, target, value in flows]

# Create chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Chart configuration
chart.options.chart = {
    "type": "sankey",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 250,
    "marginRight": 300,
    "marginTop": 220,
    "marginBottom": 250,
}

# Title
chart.options.title = {
    "text": "Titanic Survival · parallel-categories-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": "#333333"},
}

# Subtitle
chart.options.subtitle = {
    "text": "Passenger flow from Class → Sex → Age Group → Survival Outcome",
    "style": {"fontSize": "40px", "color": "#666666"},
}

# Tooltip
chart.options.tooltip = {
    "style": {"fontSize": "36px"},
    "nodeFormat": "{point.name}: {point.sum} passengers",
    "pointFormat": "{point.fromNode.name} → {point.toNode.name}: {point.weight} passengers",
}

# Series configuration for parallel categories
series_config = {
    "type": "sankey",
    "name": "Titanic Passengers",
    "keys": ["from", "to", "weight"],
    "nodes": nodes_data,
    "data": links_data,
    "dataLabels": {
        "enabled": True,
        "style": {"fontSize": "40px", "fontWeight": "bold", "color": "#333333", "textOutline": "4px #ffffff"},
        "nodeFormat": "{point.name}",
        "padding": 10,
    },
    "nodeWidth": 70,
    "nodePadding": 40,
    "linkOpacity": 0.6,
    "curveFactor": 0.5,
    "colorByPoint": True,
    "linkColorMode": "from",
    "minLinkWidth": 4,
}

chart.options.series = [series_config]

# Disable legend (nodes are labeled)
chart.options.legend = {"enabled": False}

# Disable credits
chart.options.credits = {"enabled": False}

# Accessibility options (Highcharts-specific feature)
chart.options.accessibility = {
    "enabled": True,
    "description": "Parallel categories diagram showing Titanic passenger survival rates by class, sex, and age group",
    "point": {"valueDescriptionFormat": "{point.name}: {point.sum} passengers"},
}

# Plot options for animation and better interactivity
chart.options.plot_options = {
    "sankey": {
        "animation": {"duration": 1000},
        "states": {"hover": {"linkOpacity": 0.9, "brightness": 0.1}, "inactive": {"linkOpacity": 0.2, "opacity": 0.5}},
    }
}

# Download Highcharts JS and modules
highcharts_url = "https://code.highcharts.com/highcharts.js"
sankey_url = "https://code.highcharts.com/modules/sankey.js"
accessibility_url = "https://code.highcharts.com/modules/accessibility.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(sankey_url, timeout=30) as response:
    sankey_js = response.read().decode("utf-8")

with urllib.request.urlopen(accessibility_url, timeout=30) as response:
    accessibility_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()

# Custom dimension labels at bottom
dimension_labels_html = """
<div id="dimension-labels" style="position: absolute; bottom: 60px; left: 250px; right: 300px;
     display: flex; justify-content: space-between; font-family: Arial, sans-serif;
     font-size: 52px; font-weight: bold; color: #333;">
    <span style="text-align: center; width: 25%;">Class</span>
    <span style="text-align: center; width: 25%;">Sex</span>
    <span style="text-align: center; width: 25%;">Age Group</span>
    <span style="text-align: center; width: 25%;">Outcome</span>
</div>
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{sankey_js}</script>
    <script>{accessibility_js}</script>
</head>
<body style="margin:0; position: relative;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    {dimension_labels_html}
    <script>{html_str}</script>
</body>
</html>"""

# Save HTML for interactive version (use CDN for standalone)
standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/sankey.js"></script>
    <script src="https://code.highcharts.com/modules/accessibility.js"></script>
</head>
<body style="margin:0; overflow:auto; position: relative;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    {dimension_labels_html}
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
