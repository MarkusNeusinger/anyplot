""" pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: highcharts unknown | Python 3.14.3
Quality: 80/100 | Created: 2026-03-03
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


# Data - Opinion survey tracking ~1000 respondents across 4 quarterly waves
# Categories: Strongly Agree, Agree, Neutral, Disagree, Strongly Disagree
# Topic: "Should cities invest more in public transit?"
np.random.seed(42)

waves = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
categories = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]

# Flow data: [from_node, to_node, flow_count]
# Naming convention: "{Category}_{WaveIndex}" for column positioning
flows = [
    # Q1 -> Q2: Early shifts after transit expansion announcement
    ["Strongly Agree_0", "Strongly Agree_1", 145],
    ["Strongly Agree_0", "Agree_1", 30],
    ["Strongly Agree_0", "Neutral_1", 5],
    ["Agree_0", "Strongly Agree_1", 25],
    ["Agree_0", "Agree_1", 185],
    ["Agree_0", "Neutral_1", 35],
    ["Agree_0", "Disagree_1", 5],
    ["Neutral_0", "Strongly Agree_1", 5],
    ["Neutral_0", "Agree_1", 30],
    ["Neutral_0", "Neutral_1", 120],
    ["Neutral_0", "Disagree_1", 25],
    ["Neutral_0", "Strongly Disagree_1", 5],
    ["Disagree_0", "Agree_1", 10],
    ["Disagree_0", "Neutral_1", 20],
    ["Disagree_0", "Disagree_1", 115],
    ["Disagree_0", "Strongly Disagree_1", 15],
    ["Strongly Disagree_0", "Neutral_1", 5],
    ["Strongly Disagree_0", "Disagree_1", 15],
    ["Strongly Disagree_0", "Strongly Disagree_1", 100],
    # Q2 -> Q3: After pilot program launches
    ["Strongly Agree_1", "Strongly Agree_2", 150],
    ["Strongly Agree_1", "Agree_2", 20],
    ["Strongly Agree_1", "Neutral_2", 5],
    ["Agree_1", "Strongly Agree_2", 35],
    ["Agree_1", "Agree_2", 195],
    ["Agree_1", "Neutral_2", 20],
    ["Agree_1", "Disagree_2", 5],
    ["Neutral_1", "Strongly Agree_2", 5],
    ["Neutral_1", "Agree_2", 40],
    ["Neutral_1", "Neutral_2", 110],
    ["Neutral_1", "Disagree_2", 25],
    ["Neutral_1", "Strongly Disagree_2", 5],
    ["Disagree_1", "Agree_2", 10],
    ["Disagree_1", "Neutral_2", 25],
    ["Disagree_1", "Disagree_2", 105],
    ["Disagree_1", "Strongly Disagree_2", 20],
    ["Strongly Disagree_1", "Neutral_2", 5],
    ["Strongly Disagree_1", "Disagree_2", 10],
    ["Strongly Disagree_1", "Strongly Disagree_2", 105],
    # Q3 -> Q4: After ridership data published
    ["Strongly Agree_2", "Strongly Agree_3", 165],
    ["Strongly Agree_2", "Agree_3", 20],
    ["Strongly Agree_2", "Neutral_3", 5],
    ["Agree_2", "Strongly Agree_3", 40],
    ["Agree_2", "Agree_3", 200],
    ["Agree_2", "Neutral_3", 20],
    ["Agree_2", "Disagree_3", 5],
    ["Neutral_2", "Strongly Agree_3", 5],
    ["Neutral_2", "Agree_3", 35],
    ["Neutral_2", "Neutral_3", 95],
    ["Neutral_2", "Disagree_3", 25],
    ["Neutral_2", "Strongly Disagree_3", 10],
    ["Disagree_2", "Agree_3", 10],
    ["Disagree_2", "Neutral_3", 15],
    ["Disagree_2", "Disagree_3", 100],
    ["Disagree_2", "Strongly Disagree_3", 20],
    ["Strongly Disagree_2", "Neutral_3", 5],
    ["Strongly Disagree_2", "Disagree_3", 10],
    ["Strongly Disagree_2", "Strongly Disagree_3", 115],
]

# Consistent opinion colors across all waves (colorblind-safe)
category_colors = {
    "Strongly Agree": "#1B7837",
    "Agree": "#7FBC41",
    "Neutral": "#9E9E9E",
    "Disagree": "#E08214",
    "Strongly Disagree": "#C51B7D",
}

# Column positions for strict time-based vertical ordering
column_positions = {str(i): i for i in range(len(waves))}

# Calculate totals per node for labels
node_totals = {}
for source, target, count in flows:
    node_totals[source] = node_totals.get(source, 0) + count
    node_totals[target] = node_totals.get(target, 0) + count

# For nodes that appear as both source and target, track outgoing and incoming separately
node_outgoing = {}
node_incoming = {}
for source, target, count in flows:
    node_outgoing[source] = node_outgoing.get(source, 0) + count
    node_incoming[target] = node_incoming.get(target, 0) + count

# Create nodes with column positions
nodes_data = []
for wave_idx in range(len(waves)):
    for cat in categories:
        node_id = f"{cat}_{wave_idx}"
        # Use outgoing total for first wave, incoming total for last wave, either works for middle
        if wave_idx == 0:
            total = node_outgoing.get(node_id, 0)
        else:
            total = node_incoming.get(node_id, 0)
        nodes_data.append(
            {"id": node_id, "name": f"{cat} ({total})", "column": wave_idx, "color": category_colors[cat]}
        )

# Identify stable flows (same category across waves) vs changers
# Stable flows get full opacity, changers get reduced opacity
links_data = []
for source, target, weight in flows:
    source_cat = source.rsplit("_", 1)[0]
    target_cat = target.rsplit("_", 1)[0]
    is_stable = source_cat == target_cat
    links_data.append({"from": source, "to": target, "weight": weight, "opacity": 0.6 if is_stable else 0.25})

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "sankey",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 250,
    "marginRight": 500,
    "marginTop": 200,
    "marginBottom": 200,
}

chart.options.title = {
    "text": "Public Transit Investment Opinion · alluvial-opinion-flow · highcharts · pyplots.ai",
    "style": {"fontSize": "56px", "fontWeight": "bold", "color": "#333333"},
}

chart.options.subtitle = {
    "text": '"Should cities invest more in public transit?" — 1,000 respondents tracked quarterly',
    "style": {"fontSize": "38px", "color": "#666666"},
}

chart.options.tooltip = {
    "style": {"fontSize": "32px"},
    "nodeFormat": "{point.name}: {point.sum} respondents",
    "pointFormat": "{point.fromNode.name} → {point.toNode.name}: {point.weight} respondents",
}

series_config = {
    "type": "sankey",
    "name": "Opinion Flow",
    "keys": ["from", "to", "weight"],
    "nodes": nodes_data,
    "data": links_data,
    "dataLabels": {
        "enabled": True,
        "crop": False,
        "overflow": "allow",
        "style": {"fontSize": "30px", "fontWeight": "bold", "color": "#333333", "textOutline": "3px #ffffff"},
        "nodeFormat": "{point.name}",
    },
    "nodeWidth": 55,
    "nodePadding": 40,
    "linkOpacity": 0.35,
    "curveFactor": 0.5,
    "colorByPoint": True,
    "linkColorMode": "from",
}

chart.options.series = [series_config]

# Wave labels via annotations (x-axis doesn't work with sankey)
wave_x_positions = [280, 1600, 2920, 4000]
chart.options.annotations = [
    {
        "labels": [
            {
                "point": {"x": wave_x_positions[i], "y": 2500},
                "text": wave,
                "backgroundColor": "transparent",
                "borderWidth": 0,
                "style": {"fontSize": "44px", "fontWeight": "bold", "color": "#333333"},
            }
            for i, wave in enumerate(waves)
        ],
        "labelOptions": {"useHTML": True},
    }
]

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

# Load Highcharts JS, sankey module, and annotations module
js_local_paths = {
    "highcharts": ["/tmp/hc/node_modules/highcharts/highcharts.js"],
    "sankey": ["/tmp/hc/node_modules/highcharts/modules/sankey.js"],
    "annotations": ["/tmp/hc/node_modules/highcharts/modules/annotations.js"],
}
js_cdn_urls = {
    "highcharts": "https://code.highcharts.com/highcharts.js",
    "sankey": "https://code.highcharts.com/modules/sankey.js",
    "annotations": "https://code.highcharts.com/modules/annotations.js",
}
js_modules = {}
for name in js_cdn_urls:
    loaded = False
    for local_path in js_local_paths.get(name, []):
        if Path(local_path).exists():
            js_modules[name] = Path(local_path).read_text(encoding="utf-8")
            loaded = True
            break
    if not loaded:
        req = urllib.request.Request(js_cdn_urls[name], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            js_modules[name] = response.read().decode("utf-8")

# Generate chart JS
html_str = chart.to_js_literal()

# Custom legend HTML showing opinion categories and stable vs changer distinction
legend_html = """
<div id="custom-legend" style="position: absolute; bottom: 50px; left: 50%; transform: translateX(-50%);
     display: flex; gap: 50px; font-family: Arial, sans-serif; font-size: 32px; color: #333;
     align-items: center; flex-wrap: wrap; justify-content: center;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 36px; height: 24px; background-color: #1B7837;"></div>
        <span>Strongly Agree</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 36px; height: 24px; background-color: #7FBC41;"></div>
        <span>Agree</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 36px; height: 24px; background-color: #9E9E9E;"></div>
        <span>Neutral</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 36px; height: 24px; background-color: #E08214;"></div>
        <span>Disagree</span>
    </div>
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 36px; height: 24px; background-color: #C51B7D;"></div>
        <span>Strongly Disagree</span>
    </div>
    <span style="margin-left: 30px; border-left: 2px solid #ccc; padding-left: 30px;">
        Bold flow = stable opinion &nbsp;|&nbsp; Faint flow = opinion changed
    </span>
</div>
"""

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{js_modules["highcharts"]}</script>
    <script>{js_modules["sankey"]}</script>
    <script>{js_modules["annotations"]}</script>
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
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()
