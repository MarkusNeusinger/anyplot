""" pyplots.ai
alluvial-basic: Basic Alluvial Diagram
Library: highcharts unknown | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
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


# Data - Voter migration between political parties across 3 elections
# Format: [from_node, to_node, flow_count]
# Node naming: "{Party}_{Year}" to create vertical time columns

flows = [
    # 2016 -> 2020 flows
    ["Conservative_2016", "Conservative_2020", 3200],
    ["Conservative_2016", "Moderate_2020", 800],
    ["Conservative_2016", "Progressive_2020", 200],
    ["Moderate_2016", "Conservative_2020", 600],
    ["Moderate_2016", "Moderate_2020", 2800],
    ["Moderate_2016", "Progressive_2020", 900],
    ["Progressive_2016", "Conservative_2020", 150],
    ["Progressive_2016", "Moderate_2020", 700],
    ["Progressive_2016", "Progressive_2020", 2600],
    # 2020 -> 2024 flows
    ["Conservative_2020", "Conservative_2024", 3100],
    ["Conservative_2020", "Moderate_2024", 650],
    ["Conservative_2020", "Progressive_2024", 200],
    ["Moderate_2020", "Conservative_2024", 500],
    ["Moderate_2020", "Moderate_2024", 2700],
    ["Moderate_2020", "Progressive_2024", 1100],
    ["Progressive_2020", "Conservative_2024", 100],
    ["Progressive_2020", "Moderate_2024", 550],
    ["Progressive_2020", "Progressive_2024", 3050],
]

# Colorblind-safe party colors (consistent across years)
party_colors = {
    "Conservative": "#306998",  # Python Blue
    "Moderate": "#9467BD",  # Purple
    "Progressive": "#FFD43B",  # Python Yellow
}

# Column positions for time ordering (key for alluvial structure)
column_positions = {"2016": 0, "2020": 1, "2024": 2}

# Create nodes with column positions for strict vertical ordering
nodes_data = []
for year in ["2016", "2020", "2024"]:
    for party in ["Conservative", "Moderate", "Progressive"]:
        node_id = f"{party}_{year}"
        nodes_data.append(
            {
                "id": node_id,
                "name": party,  # Display just party name
                "column": column_positions[year],
                "color": party_colors[party],
            }
        )

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
    "marginLeft": 200,
    "marginRight": 200,
    "marginTop": 200,
    "marginBottom": 150,
}

# Title
chart.options.title = {
    "text": "Voter Migration · alluvial-basic · highcharts · pyplots.ai",
    "style": {"fontSize": "64px", "fontWeight": "bold", "color": "#333333"},
}

# Subtitle with context
chart.options.subtitle = {
    "text": "Tracking voter transitions between political affiliations across election cycles (thousands of voters)",
    "style": {"fontSize": "40px", "color": "#666666"},
}

# Tooltip with units
chart.options.tooltip = {
    "style": {"fontSize": "36px"},
    "nodeFormat": "{point.name} ({point.column}): {point.sum:,.0f}K voters",
    "pointFormat": "{point.fromNode.name} → {point.toNode.name}: {point.weight:,.0f}K voters",
}

# Alluvial/Sankey series configuration with larger node labels
series_config = {
    "type": "sankey",
    "name": "Voter Flow",
    "keys": ["from", "to", "weight"],
    "nodes": nodes_data,
    "data": links_data,
    "dataLabels": {
        "enabled": True,
        "style": {"fontSize": "52px", "fontWeight": "bold", "color": "#333333", "textOutline": "4px #ffffff"},
        "nodeFormat": "{point.name}",
    },
    "nodeWidth": 60,
    "nodePadding": 45,
    "linkOpacity": 0.4,
    "curveFactor": 0.5,
    "colorByPoint": True,
    "linkColorMode": "from",
}

chart.options.series = [series_config]

# Add annotations for time point labels (x-axis doesn't work with sankey)
chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": 200 + 30, "y": 2550},  # Left column (2016)
                "text": "2016",
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "style": {"fontSize": "48px", "fontWeight": "bold", "color": "#333333"},
            },
            {
                "point": {"x": 2400, "y": 2550},  # Middle column (2020)
                "text": "2020",
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "style": {"fontSize": "48px", "fontWeight": "bold", "color": "#333333"},
            },
            {
                "point": {"x": 4600 - 30, "y": 2550},  # Right column (2024)
                "text": "2024",
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "style": {"fontSize": "48px", "fontWeight": "bold", "color": "#333333"},
            },
        ],
        "labelOptions": {"useHTML": True},
    }
]

# Enable legend for quick color reference
chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "floating": False,
    "backgroundColor": "#ffffff",
    "borderWidth": 0,
    "itemStyle": {"fontSize": "36px", "fontWeight": "normal", "color": "#333333"},
    "symbolRadius": 0,
    "symbolWidth": 40,
    "symbolHeight": 30,
    "itemMarginTop": 10,
    "itemMarginBottom": 10,
    "y": 50,
}

# Add custom legend items via a dummy series for each party
# Since sankey doesn't generate legend items by default, we use colorAxis legend simulation
# Instead, we'll add the legend data through plotOptions
chart.options.plot_options = {"sankey": {"showInLegend": True}}

# Disable credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS, sankey module, and annotations module
highcharts_url = "https://code.highcharts.com/highcharts.js"
sankey_url = "https://code.highcharts.com/modules/sankey.js"
annotations_url = "https://code.highcharts.com/modules/annotations.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

with urllib.request.urlopen(sankey_url, timeout=30) as response:
    sankey_js = response.read().decode("utf-8")

with urllib.request.urlopen(annotations_url, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()

# Create custom legend HTML since sankey doesn't support native legends well
legend_html = """
<div id="custom-legend" style="position: absolute; bottom: 60px; left: 50%; transform: translateX(-50%);
     display: flex; gap: 60px; font-family: Arial, sans-serif; font-size: 36px; color: #333;">
    <div style="display: flex; align-items: center; gap: 15px;">
        <div style="width: 40px; height: 30px; background-color: #306998;"></div>
        <span>Conservative</span>
    </div>
    <div style="display: flex; align-items: center; gap: 15px;">
        <div style="width: 40px; height: 30px; background-color: #9467BD;"></div>
        <span>Moderate</span>
    </div>
    <div style="display: flex; align-items: center; gap: 15px;">
        <div style="width: 40px; height: 30px; background-color: #FFD43B;"></div>
        <span>Progressive</span>
    </div>
</div>
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{sankey_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; position: relative;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    {legend_html}
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
    <script src="https://code.highcharts.com/modules/annotations.js"></script>
</head>
<body style="margin:0; overflow:auto; position: relative;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    {legend_html}
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
