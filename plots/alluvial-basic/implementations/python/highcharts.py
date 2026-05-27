""" anyplot.ai
alluvial-basic: Basic Alluvial Diagram
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-09
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Voter migration between political parties across 3 elections
# Format: [from_node, to_node, flow_count]
flows = [
    # 2016 -> 2020 flows
    ["Democratic_2016", "Democratic_2020", 3200],
    ["Democratic_2016", "Independent_2020", 800],
    ["Democratic_2016", "Republican_2020", 200],
    ["Independent_2016", "Democratic_2020", 600],
    ["Independent_2016", "Independent_2020", 2800],
    ["Independent_2016", "Republican_2020", 900],
    ["Republican_2016", "Democratic_2020", 150],
    ["Republican_2016", "Independent_2020", 700],
    ["Republican_2016", "Republican_2020", 2600],
    # 2020 -> 2024 flows
    ["Democratic_2020", "Democratic_2024", 3100],
    ["Democratic_2020", "Independent_2024", 650],
    ["Democratic_2020", "Republican_2024", 200],
    ["Independent_2020", "Democratic_2024", 500],
    ["Independent_2020", "Independent_2024", 2700],
    ["Independent_2020", "Republican_2024", 1100],
    ["Republican_2020", "Democratic_2024", 100],
    ["Republican_2020", "Independent_2024", 550],
    ["Republican_2020", "Republican_2024", 3050],
]

# Party colors using Okabe-Ito palette
party_colors = {
    "Democratic": IMPRINT[0],  # #009E73
    "Independent": IMPRINT[1],  # #C475FD
    "Republican": IMPRINT[2],  # #4467A3
}

# Column positions for time ordering
column_positions = {"2016": 0, "2020": 1, "2024": 2}

# Create nodes with column positions
nodes_data = []
for year in ["2016", "2020", "2024"]:
    for party in ["Democratic", "Independent", "Republican"]:
        node_id = f"{party}_{year}"
        nodes_data.append(
            {"id": node_id, "name": party, "column": column_positions[year], "color": party_colors[party]}
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
    "backgroundColor": PAGE_BG,
    "marginLeft": 200,
    "marginRight": 200,
    "marginTop": 200,
    "marginBottom": 150,
}

# Title - proper format without descriptive prefix
chart.options.title = {
    "text": "alluvial-basic · highcharts · anyplot.ai",
    "style": {"fontSize": "28px", "fontWeight": "normal", "color": INK},
}

# Subtitle with context
chart.options.subtitle = {
    "text": "Tracking voter transitions between political affiliations across election cycles",
    "style": {"fontSize": "22px", "color": INK_SOFT},
}

# Tooltip with units
chart.options.tooltip = {
    "style": {"fontSize": "18px", "color": INK},
    "nodeFormat": "{point.name} ({point.column}): {point.sum:,.0f} voters",
    "pointFormat": "{point.fromNode.name} → {point.toNode.name}: {point.weight:,.0f} voters",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
}

# Alluvial/Sankey series configuration
series_config = {
    "type": "sankey",
    "name": "Voter Flow",
    "keys": ["from", "to", "weight"],
    "nodes": nodes_data,
    "data": links_data,
    "dataLabels": {
        "enabled": True,
        "style": {"fontSize": "22px", "fontWeight": "normal", "color": INK},
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

# Add annotations for time point labels
chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": 200 + 30, "y": 2550},
                "text": "2016",
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "style": {"fontSize": "24px", "fontWeight": "normal", "color": INK},
            },
            {
                "point": {"x": 2400, "y": 2550},
                "text": "2020",
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "style": {"fontSize": "24px", "fontWeight": "normal", "color": INK},
            },
            {
                "point": {"x": 4600 - 30, "y": 2550},
                "text": "2024",
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "style": {"fontSize": "24px", "fontWeight": "normal", "color": INK},
            },
        ],
        "labelOptions": {"useHTML": True},
    }
]

# Legend for color reference
chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "floating": False,
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderWidth": 1,
    "itemStyle": {"fontSize": "18px", "fontWeight": "normal", "color": INK_SOFT},
    "symbolRadius": 0,
    "symbolWidth": 40,
    "symbolHeight": 30,
    "itemMarginTop": 10,
    "itemMarginBottom": 10,
    "y": 50,
}

chart.options.plot_options = {"sankey": {"showInLegend": True}}

# Disable credits
chart.options.credits = {"enabled": False}

# Download Highcharts JS modules from jsdelivr CDN
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"
sankey_url = "https://cdn.jsdelivr.net/npm/highcharts@11/modules/sankey.js"
annotations_url = "https://cdn.jsdelivr.net/npm/highcharts@11/modules/annotations.js"

headers = {"User-Agent": "Mozilla/5.0"}

req_hc = urllib.request.Request(highcharts_url, headers=headers)
with urllib.request.urlopen(req_hc, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

req_sankey = urllib.request.Request(sankey_url, headers=headers)
with urllib.request.urlopen(req_sankey, timeout=30) as response:
    sankey_js = response.read().decode("utf-8")

req_anno = urllib.request.Request(annotations_url, headers=headers)
with urllib.request.urlopen(req_anno, timeout=30) as response:
    annotations_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_str = chart.to_js_literal()

# Create custom legend HTML
legend_html = f"""
<div id="custom-legend" style="position: absolute; bottom: 60px; left: 50%; transform: translateX(-50%);
     display: flex; gap: 60px; font-family: Arial, sans-serif; font-size: 18px; color: {INK_SOFT};">
    <div style="display: flex; align-items: center; gap: 15px;">
        <div style="width: 40px; height: 30px; background-color: {IMPRINT[0]};"></div>
        <span>Democratic</span>
    </div>
    <div style="display: flex; align-items: center; gap: 15px;">
        <div style="width: 40px; height: 30px; background-color: {IMPRINT[1]};"></div>
        <span>Independent</span>
    </div>
    <div style="display: flex; align-items: center; gap: 15px;">
        <div style="width: 40px; height: 30px; background-color: {IMPRINT[2]};"></div>
        <span>Republican</span>
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
<body style="margin:0; position: relative; background:{PAGE_BG};">
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
<body style="margin:0; overflow:auto; position: relative; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    {legend_html}
    <script>{html_str}</script>
</body>
</html>"""

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
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
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save(f"plot-{THEME}.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
